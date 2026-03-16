from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.match import Match, MatchStatus
from app.models.innings import Innings
from app.models.team import Team
from app.schemas.match import MatchCreate, MatchToss, MatchOut

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.post("/", response_model=MatchOut)
def create_match(data: MatchCreate, db: Session = Depends(get_db)):
    if data.team1_id == data.team2_id:
        raise HTTPException(status_code=400, detail="A team cannot play against itself")
    for tid in [data.team1_id, data.team2_id]:
        if not db.query(Team).filter(Team.id == tid).first():
            raise HTTPException(status_code=404, detail=f"Team {tid} not found")
    match = Match(**data.model_dump())
    if match.date is None:
        match.date = datetime.utcnow()
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.get("/", response_model=List[MatchOut])
def list_matches(status: MatchStatus = None, db: Session = Depends(get_db)):
    q = db.query(Match)
    if status:
        q = q.filter(Match.status == status)
    return q.order_by(Match.date.desc()).all()


@router.get("/{match_id}", response_model=MatchOut)
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.post("/{match_id}/toss", response_model=MatchOut)
def record_toss(match_id: int, data: MatchToss, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status != MatchStatus.SCHEDULED:
        raise HTTPException(status_code=400, detail="Toss already done or match in progress")
    if data.toss_winner_id not in [match.team1_id, match.team2_id]:
        raise HTTPException(status_code=400, detail="Toss winner must be one of the playing teams")

    match.toss_winner_id = data.toss_winner_id
    match.toss_decision = data.toss_decision
    match.status = MatchStatus.TOSS

    # Create innings based on toss
    if data.toss_decision.value == "bat":
        bat_first = data.toss_winner_id
        bowl_first = match.team2_id if bat_first == match.team1_id else match.team1_id
    else:
        bowl_first = data.toss_winner_id
        bat_first = match.team2_id if bowl_first == match.team1_id else match.team1_id

    innings1 = Innings(
        match_id=match_id, innings_number=1,
        batting_team_id=bat_first, bowling_team_id=bowl_first
    )
    innings2 = Innings(
        match_id=match_id, innings_number=2,
        batting_team_id=bowl_first, bowling_team_id=bat_first
    )
    db.add_all([innings1, innings2])
    db.commit()
    db.refresh(match)
    return match


@router.post("/{match_id}/start", response_model=MatchOut)
def start_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status != MatchStatus.TOSS:
        raise HTTPException(status_code=400, detail="Complete toss before starting")
    match.status = MatchStatus.LIVE
    db.commit()
    db.refresh(match)
    return match


@router.post("/{match_id}/end", response_model=MatchOut)
def end_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Calculate result
    innings_list = db.query(Innings).filter(Innings.match_id == match_id).order_by(Innings.innings_number).all()
    if len(innings_list) == 2:
        inn1, inn2 = innings_list
        if inn1.total_runs > inn2.total_runs:
            match.winner_id = inn1.batting_team_id
            diff = inn1.total_runs - inn2.total_runs
            match.result_summary = f"{inn1.batting_team.name} won by {diff} runs"
        elif inn2.total_runs > inn1.total_runs:
            match.winner_id = inn2.batting_team_id
            from app.models.team import TeamPlayer
            team_size = db.query(TeamPlayer).filter(TeamPlayer.team_id == inn2.batting_team_id).count()
            wickets_remaining = max(team_size - 1, 1) - inn2.total_wickets if team_size > 0 else 10 - inn2.total_wickets
            match.result_summary = f"{inn2.batting_team.name} won by {wickets_remaining} wicket{'s' if wickets_remaining != 1 else ''}"
        else:
            match.result_summary = "Match Tied"

    for inn in innings_list:
        inn.is_completed = True

    match.status = MatchStatus.COMPLETED
    db.commit()
    db.refresh(match)
    return match


@router.post("/{match_id}/super-over", response_model=MatchOut)
def start_super_over(match_id: int, db: Session = Depends(get_db)):
    """Start a super over for a tied match."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Count existing super overs
    all_innings = db.query(Innings).filter(Innings.match_id == match_id).order_by(Innings.innings_number).all()
    next_inn_num = len(all_innings) + 1

    # Determine which team bats first in super over (team that batted 2nd bats first in SO)
    last_inn = all_innings[-1] if all_innings else None
    if last_inn:
        so_bat_first = last_inn.batting_team_id
        so_bowl_first = last_inn.bowling_team_id
    else:
        so_bat_first = match.team1_id
        so_bowl_first = match.team2_id

    # Create 2 super over innings (1 over each)
    so_inn1 = Innings(
        match_id=match_id, innings_number=next_inn_num,
        batting_team_id=so_bat_first, bowling_team_id=so_bowl_first
    )
    so_inn2 = Innings(
        match_id=match_id, innings_number=next_inn_num + 1,
        batting_team_id=so_bowl_first, bowling_team_id=so_bat_first
    )
    db.add_all([so_inn1, so_inn2])

    # Set match back to live with 1 over
    match.status = MatchStatus.LIVE
    match.result_summary = None
    match.winner_id = None

    db.commit()
    db.refresh(match)
    return match
