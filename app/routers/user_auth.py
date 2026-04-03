from fastapi import APIRouter, Depends, HTTPException, Response, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import uuid

from app.database import get_db
from app.models.user import User
from app.models.player import Player, BattingStyle, BowlingStyle
from app.schemas.user import (
    UserRegister, UserLogin, UserOut, TokenOut, ProfileUpdate,
    ForgotPasswordRequest, VerifyOtpRequest, ResetPasswordRequest,
)
from app.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user_from_cookie, generate_otp, verify_otp, send_otp_email,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads", "photos")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _map_bowling_style(hand, btype):
    """Map user bowling_hand + bowling_type to Player BowlingStyle enum."""
    if not hand or hand == 'none':
        return BowlingStyle.NONE
    arm = 'right_arm' if hand == 'right' else 'left_arm'
    type_map = {
        'fast': 'fast', 'medium': 'medium', 'offspin': 'offspin',
        'legspin': 'legspin', 'orthodox': 'orthodox', 'chinaman': 'chinaman',
    }
    style_key = type_map.get(btype, '')
    if not style_key:
        return BowlingStyle.NONE
    full = f"{arm}_{style_key}"
    try:
        return BowlingStyle(full)
    except ValueError:
        return BowlingStyle.NONE


def sync_user_to_player(user, db: Session):
    """Create or update a Player record linked to this user."""
    bat = BattingStyle.LEFT_HAND if user.batting_hand == 'left' else BattingStyle.RIGHT_HAND
    bowl = _map_bowling_style(user.bowling_hand, user.bowling_type)

    player = db.query(Player).filter(Player.user_id == user.id).first()
    if player:
        player.name = user.name
        player.nickname = user.nickname
        player.batting_style = bat
        player.bowling_style = bowl
        player.phone = user.phone
        player.player_role = user.player_role
    else:
        player = Player(
            name=user.name,
            nickname=user.nickname,
            batting_style=bat,
            bowling_style=bowl,
            phone=user.phone,
            player_role=user.player_role,
            user_id=user.id,
        )
        db.add(player)
    db.commit()

router = APIRouter(prefix="/api/user", tags=["User Auth"])


@router.post("/register", response_model=TokenOut)
def register(data: UserRegister, response: Response, db: Session = Depends(get_db)):
    # Validate
    if not data.name or len(data.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
    if not data.email or "@" not in data.email:
        raise HTTPException(status_code=400, detail="Valid email is required")
    if not data.password or len(data.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    existing = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=data.name.strip(),
        email=data.email.lower().strip(),
        phone=data.phone,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email)
    response.set_cookie(
        key="boxcric_token", value=token,
        httponly=True, max_age=365 * 24 * 3600, samesite="lax"
    )
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(user.id, user.email)
    response.set_cookie(
        key="boxcric_token", value=token,
        httponly=True, max_age=365 * 24 * 3600, samesite="lax"
    )
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("boxcric_token")
    return {"detail": "Logged out"}


@router.get("/all", response_model=list[UserOut])
def list_all_users(db: Session = Depends(get_db)):
    """List all registered users."""
    return db.query(User).order_by(User.created_at.desc()).all()


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user and clean up all references."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete photo file if exists
    if user.photo:
        photo_path = os.path.join(BASE_DIR, user.photo.lstrip("/"))
        if os.path.exists(photo_path):
            os.remove(photo_path)

    from sqlalchemy import text
    # Clean up all FK references using raw SQL
    db.execute(text("UPDATE players SET user_id = NULL WHERE user_id = :uid"), {"uid": user_id})
    db.execute(text("UPDATE teams SET host_id = NULL WHERE host_id = :uid"), {"uid": user_id})
    db.execute(text("UPDATE teams SET cohost_id = NULL WHERE cohost_id = :uid"), {"uid": user_id})
    db.execute(text("DELETE FROM notifications WHERE user_id = :uid"), {"uid": user_id})
    db.execute(text("DELETE FROM match_predictions WHERE user_id = :uid"), {"uid": user_id})
    db.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
    db.commit()
    return {"detail": f"User '{user.name}' deleted"}


@router.get("/me", response_model=UserOut)
def get_me(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.post("/profile", response_model=UserOut)
def update_profile(data: ProfileUpdate, request: Request, db: Session = Depends(get_db)):
    """Update user profile. Full edits limited to 5 times. Age, height always editable."""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Require role fields on first profile save (or if not yet set)
    if not user.profile_complete:
        missing = []
        if not data.gender and not user.gender:
            missing.append("Gender")
        if not data.player_role and not user.player_role:
            missing.append("Playing Role")
        if not data.batting_hand and not user.batting_hand:
            missing.append("Batting Hand")
        if not data.bowling_hand and not user.bowling_hand:
            missing.append("Bowling Hand")
        if missing:
            raise HTTPException(status_code=400, detail=f"Please select: {', '.join(missing)}")

    # Always allowed: name, nickname, age, height
    if data.name is not None and len(data.name.strip()) >= 2:
        user.name = data.name.strip()
    if data.nickname is not None:
        user.nickname = data.nickname.strip() or None
    if data.age is not None:
        user.age = data.age
    if data.height is not None:
        user.height = data.height

    # Restricted fields: check if any are changing
    restricted_changed = False
    restricted_fields = {
        "batting_hand": data.batting_hand,
        "bowling_hand": data.bowling_hand,
        "bowling_type": data.bowling_type,
        "gender": data.gender,
        "player_role": data.player_role,
    }

    for field, value in restricted_fields.items():
        if value is not None:
            current = getattr(user, field, None)
            if current != value:
                restricted_changed = True
                break

    if restricted_changed:
        if user.profile_edits >= 5:
            raise HTTPException(
                status_code=400,
                detail="Profile edit limit reached (5/5). You can only update age, height, and photo now."
            )
        # Apply restricted fields
        if data.batting_hand is not None:
            user.batting_hand = data.batting_hand
        if data.bowling_hand is not None:
            user.bowling_hand = data.bowling_hand
        if data.bowling_type is not None:
            user.bowling_type = data.bowling_type
        if data.gender is not None:
            user.gender = data.gender
        if data.player_role is not None:
            user.player_role = data.player_role
        user.profile_edits = (user.profile_edits or 0) + 1

    user.profile_complete = True
    db.commit()
    db.refresh(user)

    # Sync user profile to linked Player record
    try:
        sync_user_to_player(user, db)
    except Exception as e:
        print(f"[SYNC] Warning: {e}")

    return user


@router.post("/photo", response_model=UserOut)
async def upload_photo(request: Request, photo: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload profile photo."""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Validate file type
    if photo.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, WEBP allowed")

    # Save file
    ext = photo.filename.rsplit(".", 1)[-1] if "." in photo.filename else "jpg"
    filename = f"{user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    contents = await photo.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Photo must be under 5MB")

    with open(filepath, "wb") as f:
        f.write(contents)

    # Delete old photo if exists
    if user.photo:
        old_path = os.path.join(BASE_DIR, user.photo.lstrip("/"))
        if os.path.exists(old_path):
            os.remove(old_path)

    user.photo = f"/static/uploads/photos/{filename}"
    db.commit()
    db.refresh(user)
    return user


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send OTP to email. Auto-registers if email not found (new user)."""
    email = data.email.strip().lower() if data.email else ""
    phone = data.phone.strip() if data.phone else ""
    
    if not email and not phone:
        raise HTTPException(status_code=400, detail="Email or phone is required")
    
    # Look up user by email first, then phone
    user = None
    if email:
        user = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user and phone:
        user = db.query(User).filter(User.phone == phone, User.is_active == True).first()
    
    # Auto-register if not found
    if not user:
        if not email:
            email = f"{phone}@boxcric.local"
        user = User(
            name="New User",
            email=email,
            phone=phone,
            hashed_password=hash_password("boxcric_auto"),
            profile_complete=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Use email as OTP key
    otp_key = user.email
    otp = generate_otp(otp_key, user.id)
    
    # Try to send via email
    email_sent = send_otp_email(user.email, otp, user.name)
    
    result = {
        "detail": f"OTP sent to {user.email}" if email_sent else f"OTP generated (email not configured)",
        "email_sent": email_sent,
        "expires_in_minutes": 5,
        "user_name": user.name,
        "is_new_user": not user.profile_complete,
        "otp_key": otp_key,
    }
    # If email not configured, include OTP in response so login still works (demo mode)
    if not email_sent:
        result["demo_otp"] = otp
        print(f"[OTP] {otp_key}: {otp} (email not configured — demo mode)")
    return result


@router.post("/verify-otp", response_model=TokenOut)
def verify_otp_endpoint(data: VerifyOtpRequest, response: Response, db: Session = Depends(get_db)):
    """Verify OTP and log the user in."""
    otp_key = data.email.strip().lower() if data.email else data.phone.strip()
    user_id = verify_otp(otp_key, data.otp.strip())
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = create_access_token(user.id, user.email)
    response.set_cookie(
        key="boxcric_token", value=token,
        httponly=True, max_age=365 * 24 * 3600, samesite="lax"
    )
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Verify OTP and set a new password."""
    phone = data.phone.strip()
    if not data.new_password or len(data.new_password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    user_id = verify_otp(phone, data.otp.strip())
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"detail": "Password reset successfully. You can now login."}


@router.post("/admin/bootstrap")
def bootstrap_first_admin(request: Request, db: Session = Depends(get_db)):
    """Make the current logged-in user the first admin. Only works if no admins exist."""
    existing_admin = db.query(User).filter(User.is_admin == True).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="An admin already exists")
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login first")
    user.is_admin = True
    db.commit()
    return {"detail": f"{user.name} is now the first admin"}
