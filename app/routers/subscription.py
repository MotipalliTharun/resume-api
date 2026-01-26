from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import User
from services.auth_service import get_current_active_user
from pydantic import BaseModel

router = APIRouter(
    prefix="/subscription",
    tags=["subscription"],
)

class PlanUpgrade(BaseModel):
    plan_name: str # "pro", "enterprise"

@router.get("/plans")
def get_plans():
    return [
        {"id": "free", "name": "Starter", "price": 0},
        {"id": "pro", "name": "Pro", "price": 19},
        {"id": "enterprise", "name": "Naval Ravikant Edition", "price": 49},
    ]

@router.post("/upgrade")
def upgrade_plan(
    plan: PlanUpgrade, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Mock payment processing
    if plan.plan_name not in ["pro", "enterprise", "free"]:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    current_user.subscription_tier = plan.plan_name
    db.commit()
    
    return {"status": "success", "new_tier": current_user.subscription_tier}
