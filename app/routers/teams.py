from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.team import Team, TeamPlayer
from app.models.player import Player
from app.schemas.team import TeamCreate, TeamUpdate, TeamAddPlayer, TeamSetCaptain, TeamOut

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.post("/", response_model=TeamOut)
def create_team(data: TeamCreate, db: Session = Depends(get_db)):
    team = Team(**data.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("/", response_model=List[TeamOut])
def list_teams(db: Session = Depends(get_db)):
    return db.query(Team).all()


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.put("/{team_id}", response_model=TeamOut)
def update_team(team_id: int, data: TeamUpdate, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(team, field, value)
    db.commit()
    db.refresh(team)
    return team


@router.post("/{team_id}/players", response_model=TeamOut)
def add_player_to_team(team_id: int, data: TeamAddPlayer, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    player = db.query(Player).filter(Player.id == data.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    existing = db.query(TeamPlayer).filter(
        TeamPlayer.team_id == team_id,
        TeamPlayer.player_id == data.player_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Player already in team")
    tp = TeamPlayer(team_id=team_id, player_id=data.player_id)
    db.add(tp)
    db.commit()
    db.refresh(team)
    return team


@router.delete("/{team_id}/players/{player_id}", response_model=TeamOut)
def remove_player_from_team(team_id: int, player_id: int, db: Session = Depends(get_db)):
    tp = db.query(TeamPlayer).filter(
        TeamPlayer.team_id == team_id,
        TeamPlayer.player_id == player_id
    ).first()
    if not tp:
        raise HTTPException(status_code=404, detail="Player not in team")
    db.delete(tp)
    db.commit()
    team = db.query(Team).filter(Team.id == team_id).first()
    return team


@router.delete("/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    db.query(TeamPlayer).filter(TeamPlayer.team_id == team_id).delete()
    db.delete(team)
    db.commit()
    return {"detail": "Team deleted"}


@router.post("/{team_id}/captain", response_model=TeamOut)
def set_captain(team_id: int, data: TeamSetCaptain, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if data.captain_id is not None:
        team.captain_id = data.captain_id if data.captain_id > 0 else None
    if data.vice_captain_id is not None:
        team.vice_captain_id = data.vice_captain_id if data.vice_captain_id > 0 else None
    db.commit()
    db.refresh(team)
    return team
