import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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

# Email config — Gmail SMTP (free 500 emails/day)
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")  # e.g. yourname@gmail.com
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # Gmail App Password
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# In-memory OTP store: { identifier: { "otp": "123456", "expires": datetime, "user_id": int } }
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


def generate_otp(identifier: str, user_id: int) -> str:
    """Generate a 6-digit OTP for the given identifier (email or phone)."""
    otp = str(random.randint(100000, 999999))
    _otp_store[identifier] = {
        "otp": otp,
        "expires": datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES),
        "user_id": user_id,
    }
    return otp


def send_otp_email(to_email: str, otp: str, user_name: str = "User") -> bool:
    """Send OTP via Gmail SMTP. Returns True if sent, False otherwise."""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"BOXcric <{SMTP_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = f"BOXcric Login OTP: {otp}"

        html = f"""\
        <div style="font-family:Arial,sans-serif;max-width:400px;margin:0 auto;padding:20px">
          <div style="text-align:center;margin-bottom:20px">
            <h1 style="color:#1a472a;margin:0">🏏 BOXcric</h1>
            <p style="color:#6c757d;font-size:14px">Cricket Match Management</p>
          </div>
          <div style="background:#f0fdf4;border:2px solid #1a472a;border-radius:12px;padding:24px;text-align:center">
            <p style="margin:0 0 8px;color:#333">Hi {user_name},</p>
            <p style="margin:0 0 16px;color:#666;font-size:14px">Your login OTP is:</p>
            <div style="font-size:36px;font-weight:800;letter-spacing:8px;color:#1a472a;margin:12px 0">{otp}</div>
            <p style="margin:16px 0 0;color:#999;font-size:12px">Expires in 5 minutes. Do not share.</p>
          </div>
        </div>"""
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False


def verify_otp(identifier: str, otp: str) -> int | None:
    """Verify OTP for identifier. Returns user_id if valid, None otherwise."""
    entry = _otp_store.get(identifier)
    if not entry:
        return None
    if datetime.utcnow() > entry["expires"]:
        _otp_store.pop(identifier, None)
        return None
    if entry["otp"] != otp:
        return None
    # OTP is valid — consume it
    user_id = entry["user_id"]
    _otp_store.pop(identifier, None)
    return user_id
