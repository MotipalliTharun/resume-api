from sqlalchemy.orm import Session
from db import SessionLocal, engine
from models import User
import sys

def upgrade_user(email: str, tier: str = "pro"):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User {email} not found!")
            return
        
        print(f"Found user: {user.email} (Current Tier: {user.subscription_tier})")
        user.subscription_tier = tier
        db.commit()
        db.refresh(user)
        print(f"User {email} successfully upgraded to {user.subscription_tier}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    email = "motipallitharun@gmail.com"
    if len(sys.argv) > 1:
        email = sys.argv[1]
    
    upgrade_user(email)
