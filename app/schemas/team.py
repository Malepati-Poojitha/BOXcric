from pydantic import BaseModel
from typing import Optional, List
from app.schemas.player import PlayerOut


class TeamCreate(BaseModel):
    name: str
    short_name: Optional[str] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    captain_id: Optional[int] = None
    vice_captain_id: Optional[int] = None


class TeamAddPlayer(BaseModel):
    player_id: int


class TeamSetCaptain(BaseModel):
    captain_id: Optional[int] = None
    vice_captain_id: Optional[int] = None


class TeamSetHost(BaseModel):
    host_id: Optional[int] = None
    cohost_id: Optional[int] = None


class TeamOut(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None
    captain_id: Optional[int] = None
    vice_captain_id: Optional[int] = None
    host_id: Optional[int] = None
    cohost_id: Optional[int] = None
    captain: Optional[PlayerOut] = None
    vice_captain: Optional[PlayerOut] = None
    players: List[PlayerOut] = []

    model_config = {"from_attributes": True}
