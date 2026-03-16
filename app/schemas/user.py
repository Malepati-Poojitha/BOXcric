from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    photo: Optional[str] = None
    age: Optional[int] = None
    height: Optional[str] = None
    batting_hand: Optional[str] = None
    bowling_hand: Optional[str] = None
    bowling_type: Optional[str] = None
    gender: Optional[str] = None
    player_role: Optional[str] = None
    profile_complete: bool = False
    profile_edits: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    age: Optional[int] = None
    height: Optional[str] = None
    batting_hand: Optional[str] = None
    bowling_hand: Optional[str] = None
    bowling_type: Optional[str] = None
    gender: Optional[str] = None
    player_role: Optional[str] = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ForgotPasswordRequest(BaseModel):
    phone: str


class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str


class ResetPasswordRequest(BaseModel):
    phone: str
    otp: str
    new_password: str
