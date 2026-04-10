import os
import random
import json
import ssl
import urllib.request
import urllib.error
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

# Email config — Brevo HTTP API (free 300 emails/day)
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "")

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


def require_admin(request: Request, db: Session = Depends(get_db)):
    """Require the current user to be an admin. Raises 403 if not."""
    user = get_current_user_from_cookie(request, db)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
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
    """Send OTP via Brevo HTTP API. Returns True if sent, False otherwise."""
    if not BREVO_API_KEY or not BREVO_SENDER_EMAIL:
        print(f"[EMAIL] Brevo not configured. API_KEY={'set' if BREVO_API_KEY else 'empty'}, SENDER={'set' if BREVO_SENDER_EMAIL else 'empty'}")
        return False
    try:
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

        payload = json.dumps({
            "sender": {"name": "BOXcric", "email": BREVO_SENDER_EMAIL},
            "to": [{"email": to_email, "name": user_name}],
            "subject": f"BOXcric Login OTP: {otp}",
            "htmlContent": html
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=payload,
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            method="POST"
        )
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            resp.read()
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"Email send failed: HTTP {e.code} - {body}")
        return False
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
