from fastapi import Header, HTTPException, Depends
from passlib.context import CryptContext
from config import settings
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def verify_access_token(x_access_token: str = Header(None, alias="X-Access-Token")):
    """
    Verifies the access token (password) against the configured hash.
    If no hash is configured, access is open (or we could default to closed).
    Current logic: If hash is set, require token.
    """
    if not settings.app_password_hash:
        # If no password configured, likely development or open.
        # Warn or allow. For now, allow.
        return True

    if not x_access_token:
        raise HTTPException(status_code=401, detail="Missing Access Token")

    if not verify_password(x_access_token, settings.app_password_hash):
        raise HTTPException(status_code=401, detail="Invalid Access Token")
    
    return True
