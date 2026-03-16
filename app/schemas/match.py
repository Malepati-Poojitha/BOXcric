from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.match import MatchStatus, TossDecision


class MatchCreate(BaseModel):
    title: Optional[str] = None
    team1_id: int
    team2_id: int
    overs: int = 20
    venue: Optional[str] = None
    date: Optional[datetime] = None


class MatchToss(BaseModel):
    toss_winner_id: int
    toss_decision: TossDecision


class InningsOut(BaseModel):
    id: int
    innings_number: int
    batting_team_id: int
    bowling_team_id: int
    total_runs: int
    total_wickets: int
    total_overs: int
    total_balls: int
    extras: int
    is_completed: bool

    model_config = {"from_attributes": True}


class MatchOut(BaseModel):
    id: int
    title: Optional[str] = None
    team1_id: int
    team2_id: int
    overs: int
    venue: Optional[str] = None
    date: Optional[datetime] = None
    status: MatchStatus
    toss_winner_id: Optional[int] = None
    toss_decision: Optional[TossDecision] = None
    winner_id: Optional[int] = None
    result_summary: Optional[str] = None
    innings: List[InningsOut] = []

    model_config = {"from_attributes": True}
