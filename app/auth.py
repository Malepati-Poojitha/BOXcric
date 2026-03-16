import os
import random
from datetime import datetime, timedelta
import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

SECRET_KEY = os.getenv("SECRET_KEY", "boxcric-secret-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8760  # 365 days — stay logged in
OTP_EXPIRE_MINUTES = 5

# In-memory OTP store: { phone: { "otp": "123456", "expires": datetime, "user_id": int } }
_otp_store: dict[str, dict] = {}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    """Extract user from auth cookie. Returns None if not logged in."""
    token = request.cookies.get("boxcric_token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return user


def generate_otp(phone: str, user_id: int) -> str:
    """Generate a 6-digit OTP for the given phone number."""
    otp = str(random.randint(100000, 999999))
    _otp_store[phone] = {
        "otp": otp,
        "expires": datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES),
        "user_id": user_id,
    }
    return otp


def verify_otp(phone: str, otp: str) -> int | None:
    """Verify OTP for phone. Returns user_id if valid, None otherwise."""
    entry = _otp_store.get(phone)
    if not entry:
        return None
    if datetime.utcnow() > entry["expires"]:
        _otp_store.pop(phone, None)
        return None
    if entry["otp"] != otp:
        return None
    # OTP is valid — consume it
    user_id = entry["user_id"]
    _otp_store.pop(phone, None)
    return user_id
