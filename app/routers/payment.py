from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from db import get_db
from models import User
from services.auth_service import get_current_active_user
from pydantic import BaseModel
import stripe
import os

router = APIRouter(
    prefix="/payment",
    tags=["payment"],
)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class CheckoutSessionRequest(BaseModel):
    plan_id: str # "pro", "enterprise" or straight price_id

def get_or_create_customer(db: Session, user: User) -> str:
    if user.stripe_customer_id:
        return user.stripe_customer_id
    
    try:
        # Create new customer in Stripe
        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name,
            metadata={"user_id": user.id}
        )
        user.stripe_customer_id = customer.id
        db.commit()
        return customer.id
    except Exception as e:
        print(f"Stripe Customer Create Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment profile")

@router.post("/create-checkout-session")
def create_checkout_session(
    request: CheckoutSessionRequest, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Map simple plan names to Price IDs (Configured in .env or hardcoded)
        # In production, fetch from DB or usage a config mapping
        prices = {
            "pro": "price_1Q5...", # Replace!
            "enterprise": "price_1Q5..." # Replace!
        }
        
        # Determine Price ID
        price_id = prices.get(request.plan_id, request.plan_id)
        
        # Ensure Customer Exists
        customer_id = get_or_create_customer(db, current_user)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

        checkout_session = stripe.checkout.Session.create(
            mode='subscription',
            customer=customer_id,
            line_items=[
                {
                    'price': price_id, 
                    'quantity': 1,
                },
            ],
            success_url=f'{frontend_url}/app/subscription/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{frontend_url}/app/subscription?canceled=true',
            metadata={
                'user_id': current_user.id,
                'plan': request.plan_id
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"url": checkout_session.url}

@router.post("/webhook")
async def webhook(request: Request, stripe_signature: str = Header(None), db: Session = Depends(get_db)):
    payload = await request.body()
    endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, endpoint_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle Events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # This is where we link the new subscription to the user in DB
        # But we might also rely on customer.subscription.created/updated
        # 'checkout.session.completed' guarantees the flow is done.
        
        # Retrieve full subscription details
        sub_id = session.get('subscription')
        if sub_id:
            await sync_subscription(sub_id, db)

    elif event['type'] in ['customer.subscription.updated', 'customer.subscription.deleted', 'customer.subscription.created']:
        sub = event['data']['object']
        await handle_subscription_change(sub, db)
        
    elif event['type'] == 'invoice.payment_succeeded':
        # Extend access
        invoice = event['data']['object']
        sub_id = invoice.get('subscription')
        if sub_id:
             await sync_subscription(sub_id, db)

    elif event['type'] == 'invoice.payment_failed':
        # Mark past due
        # Logic handled inside sync_subscription typically via status check
        pass

    return {"status": "success"}

from models import Subscription
from datetime import datetime

async def handle_subscription_change(stripe_sub, db: Session):
    # Stripe Sub Object -> DB Upsert
    stripe_id = stripe_sub['id']
    customer_id = stripe_sub['customer']
    status = stripe_sub['status']
    current_period_end = datetime.fromtimestamp(stripe_sub['current_period_end'])
    price_id = stripe_sub['items']['data'][0]['price']['id']
    cancel_at_period_end = stripe_sub['cancel_at_period_end']
    
    # Find user by strip_customer_id
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        print(f"Webhook Error: User not found for customer {customer_id}")
        return

    # Upsert Subscription
    db_sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == stripe_id).first()
    
    if not db_sub:
        db_sub = Subscription(
            user_id=user.id,
            stripe_subscription_id=stripe_id,
        )
        db.add(db_sub)
    
    # Update fields
    db_sub.status = status
    db_sub.price_id = price_id
    db_sub.current_period_end = current_period_end
    db_sub.cancel_at_period_end = cancel_at_period_end
    
    # Mirror status to User.subscription_tier for easy gating
    # Logic: if status is active/trialing -> "pro", else "free"
    # Or map price_id to "pro"/"enterprise"
    if status in ['active', 'trialing']:
        # TODO: Lookup plan name by price_id if possible, or just set generic "premium"
        # For now, simplistic mapping:
        user.subscription_tier = "pro" 
    else:
        # Only downgrade if they don't have another active sub? 
        # Assuming 1 sub per user for now
        user.subscription_tier = "free"

    db.commit()

async def sync_subscription(sub_id: str, db: Session):
    sub = stripe.Subscription.retrieve(sub_id)
    await handle_subscription_change(sub, db)
