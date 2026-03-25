from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.player import Player
from app.schemas.player import PlayerCreate, PlayerUpdate, PlayerOut

router = APIRouter(prefix="/players", tags=["Players"])


@router.post("/", response_model=PlayerOut)
def create_player(data: PlayerCreate, db: Session = Depends(get_db)):
    player = Player(**data.model_dump())
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@router.get("/", response_model=List[PlayerOut])
def list_players(db: Session = Depends(get_db)):
    return db.query(Player).all()


@router.get("/{player_id}", response_model=PlayerOut)
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.put("/{player_id}", response_model=PlayerOut)
def update_player(player_id: int, data: PlayerUpdate, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(player, field, value)
    db.commit()
    db.refresh(player)
    return player


@router.delete("/{player_id}")
def delete_player(player_id: int, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    # Remove player from all teams
    from app.models.team import TeamPlayer, Team
    for tp in db.query(TeamPlayer).filter(TeamPlayer.player_id == player_id).all():
        db.delete(tp)
    # Clear captain/vice_captain references
    for team in db.query(Team).filter(Team.captain_id == player_id).all():
        team.captain_id = None
    for team in db.query(Team).filter(Team.vice_captain_id == player_id).all():
        team.vice_captain_id = None
    # Remove MOM votes and milestones
    from app.models.extras import MOMVote, Milestone
    for v in db.query(MOMVote).filter(MOMVote.player_id == player_id).all():
        db.delete(v)
    for m in db.query(Milestone).filter(Milestone.player_id == player_id).all():
        db.delete(m)
    db.delete(player)
    db.commit()
    return {"detail": "Player deleted"}
