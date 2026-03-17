from pydantic import BaseModel
from typing import Optional
from app.models.player import BattingStyle, BowlingStyle


class PlayerCreate(BaseModel):
    name: str
    nickname: Optional[str] = None
    batting_style: BattingStyle = BattingStyle.RIGHT_HAND
    bowling_style: BowlingStyle = BowlingStyle.NONE
    phone: Optional[str] = None
    player_role: Optional[str] = None


class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    batting_style: Optional[BattingStyle] = None
    bowling_style: Optional[BowlingStyle] = None
    phone: Optional[str] = None
    player_role: Optional[str] = None


class PlayerOut(BaseModel):
    id: int
    name: str
    nickname: Optional[str] = None
    batting_style: BattingStyle
    bowling_style: BowlingStyle
    phone: Optional[str] = None
    player_role: Optional[str] = None
    user_id: Optional[int] = None

    model_config = {"from_attributes": True}
