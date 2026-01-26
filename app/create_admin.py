from sqlalchemy.orm import Session
from db import SessionLocal, engine
from models import User
from services.auth_service import get_password_hash # Assuming this is available
import sys

# If hash function isn't easily importable, simple bcrypt here
import bcrypt
def get_password_hash_direct(password):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def create_admin_user():
    db = SessionLocal()
    email = "motipallitharun@gmail.com"
    password = "Mt@3218020970" # Use stronger password in real life
    
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        print(f"User {email} already exists.")
        return

    hashed_password = get_password_hash_direct(password)
    
    new_user = User(
        email=email,
        hashed_password=hashed_password,
        full_name="Admin User",
        is_active=True,
        subscription_tier="enterprise" # Give admin enterprise access
    )
    
    db.add(new_user)
    db.commit()
    print(f"Admin user {email} created successfully.")
    db.close()

if __name__ == "__main__":
    create_admin_user()
