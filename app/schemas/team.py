from pydantic import BaseModel
from typing import Optional, List
from app.schemas.player import PlayerOut


class TeamCreate(BaseModel):
    name: str
    short_name: Optional[str] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None


class TeamAddPlayer(BaseModel):
    player_id: int


class TeamOut(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None
    players: List[PlayerOut] = []

    model_config = {"from_attributes": True}
