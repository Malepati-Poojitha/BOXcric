from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ball import Ball
from app.schemas.score import BallInput, BallOut, LiveScoreOut, ScorecardOut
from app.services.scoring import record_ball, get_live_score, get_scorecard

router = APIRouter(prefix="/scoring", tags=["Live Scoring"])


@router.post("/innings/{innings_id}/ball", response_model=BallOut)
def add_ball(innings_id: int, data: BallInput, db: Session = Depends(get_db)):
    """Record a ball delivery for live scoring."""
    try:
        ball = record_ball(db, innings_id, data)
        return ball
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/match/{match_id}/live", response_model=LiveScoreOut)
def live_score(match_id: int, db: Session = Depends(get_db)):
    """Get live score for a match."""
    try:
        return get_live_score(db, match_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/innings/{innings_id}/scorecard", response_model=ScorecardOut)
def scorecard(innings_id: int, db: Session = Depends(get_db)):
    """Get full scorecard for an innings."""
    try:
        return get_scorecard(db, innings_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/innings/{innings_id}/lastball")
def last_ball(innings_id: int, db: Session = Depends(get_db)):
    """Get last ball info — who was batting/bowling."""
    ball = db.query(Ball).filter(Ball.innings_id == innings_id).order_by(Ball.id.desc()).first()
    if not ball:
        return {"striker": None, "non_striker": None, "bowler": None}

    # Find who's dismissed in this innings
    dismissed = set()
    all_balls = db.query(Ball).filter(Ball.innings_id == innings_id).all()
    for b in all_balls:
        if b.is_wicket and b.dismissed_player_id:
            dismissed.add(b.dismissed_player_id)

    striker_id = ball.batter_id if ball.batter_id not in dismissed else None
    non_striker_id = ball.non_striker_id if ball.non_striker_id and ball.non_striker_id not in dismissed else None
    bowler_id = ball.bowler_id

    # Check last-man-standing situation
    from app.models.innings import Innings
    from app.models.team import TeamPlayer
    inn = db.query(Innings).filter(Innings.id == innings_id).first()
    team_size = db.query(TeamPlayer).filter(TeamPlayer.team_id == inn.batting_team_id).count() if inn else 0
    max_wickets = max(team_size - 1, 1) if team_size > 0 else 10
    wickets_fallen = sum(1 for b in all_balls if b.is_wicket)
    last_man_standing = (wickets_fallen >= max_wickets - 1) and (wickets_fallen < max_wickets)

    return {
        "striker": striker_id,
        "non_striker": non_striker_id,
        "bowler": bowler_id,
        "dismissed": list(dismissed),
        "wickets_fallen": wickets_fallen,
        "max_wickets": max_wickets,
        "team_size": team_size,
        "last_man_standing": last_man_standing,
    }


@router.get("/match/{match_id}/graph")
def match_graph(match_id: int, db: Session = Depends(get_db)):
    """Get over-by-over runs & wickets for both innings — for graph display."""
    from app.models.innings import Innings
    innings_list = db.query(Innings).filter(Innings.match_id == match_id).order_by(Innings.innings_number).all()
    result = {}

    for inn in innings_list:
        balls = db.query(Ball).filter(Ball.innings_id == inn.id).order_by(Ball.id).all()
        overs = {}
        cumulative = 0
        total_wickets = 0

        for b in balls:
            ov = b.over_number
            if ov not in overs:
                overs[ov] = {"over": ov + 1, "runs": 0, "wickets": 0, "dots": 0, "fours": 0, "sixes": 0, "extras": 0}
            overs[ov]["runs"] += b.runs_scored + b.extra_runs
            if b.is_wicket:
                overs[ov]["wickets"] += 1
            if b.runs_scored == 0 and not b.is_wicket and (not b.extra_type or b.extra_type.value == "none"):
                overs[ov]["dots"] += 1
            if b.runs_scored == 4:
                overs[ov]["fours"] += 1
            if b.runs_scored == 6:
                overs[ov]["sixes"] += 1
            if b.extra_type and b.extra_type.value != "none":
                overs[ov]["extras"] += b.extra_runs

        # Build cumulative data
        over_data = []
        cumulative = 0
        total_wickets = 0
        for ov_num in sorted(overs.keys()):
            d = overs[ov_num]
            cumulative += d["runs"]
            total_wickets += d["wickets"]
            over_data.append({
                "over": d["over"],
                "runs_this_over": d["runs"],
                "cumulative_runs": cumulative,
                "wickets_this_over": d["wickets"],
                "total_wickets": total_wickets,
                "dots": d["dots"],
                "fours": d["fours"],
                "sixes": d["sixes"],
                "extras": d["extras"],
                "run_rate": round(cumulative / d["over"], 2),
            })

        key = f"innings_{inn.innings_number}"
        result[key] = {
            "innings_number": inn.innings_number,
            "batting_team_id": inn.batting_team_id,
            "total": cumulative,
            "wickets": total_wickets,
            "overs": over_data,
        }

    return result
