from pydantic import BaseModel
from typing import Optional, List
from app.models.ball import ExtraType, WicketType


class BallInput(BaseModel):
    batter_id: int
    bowler_id: int
    non_striker_id: Optional[int] = None
    runs_scored: int = 0
    extra_type: ExtraType = ExtraType.NONE
    extra_runs: int = 0
    is_wicket: bool = False
    wicket_type: WicketType = WicketType.NONE
    dismissed_player_id: Optional[int] = None
    fielder_id: Optional[int] = None
    is_correction: bool = False


class BallOut(BaseModel):
    id: int
    over_number: int
    ball_number: int
    batter_id: int
    bowler_id: int
    runs_scored: int
    extra_type: ExtraType
    extra_runs: int
    is_wicket: bool
    wicket_type: WicketType
    is_legal: bool

    model_config = {"from_attributes": True}


class LiveScoreOut(BaseModel):
    match_id: int
    innings_number: int
    batting_team: str
    bowling_team: str
    total_runs: int
    total_wickets: int
    overs: str  # e.g., "12.4"
    run_rate: float
    target: Optional[int] = None
    required_rate: Optional[float] = None
    last_ball: Optional[str] = None
    status: str


class BatterStatsOut(BaseModel):
    player_id: int
    player_name: str
    runs: int
    balls_faced: int
    fours: int
    sixes: int
    strike_rate: float
    dismissal: str = "not out"


class BowlerStatsOut(BaseModel):
    player_id: int
    player_name: str
    overs: str
    maidens: int
    runs_conceded: int
    wickets: int
    economy: float


class ScorecardOut(BaseModel):
    match_id: int
    innings_number: int
    batting_team: str
    total_runs: int
    total_wickets: int
    overs: str
    batters: List[BatterStatsOut]
    bowlers: List[BowlerStatsOut]


class PlayerCareerStats(BaseModel):
    player_id: int
    player_name: str
    matches: int
    # Batting
    total_runs: int
    innings_batted: int
    not_outs: int
    highest_score: int
    batting_average: float
    strike_rate: float
    fifties: int
    hundreds: int
    fours: int
    sixes: int
    # Bowling
    total_wickets: int
    innings_bowled: int
    balls_bowled: int
    runs_conceded: int
    best_bowling: str
    bowling_average: float
    economy: float


class RecordOut(BaseModel):
    category: str
    value: str
    player_name: Optional[str] = None
    team_name: Optional[str] = None
    match_info: Optional[str] = None
