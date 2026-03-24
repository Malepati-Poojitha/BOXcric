from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.player import Player
from app.schemas.player import PlayerCreate, PlayerUpdate, PlayerOut
from app.auth import require_admin

router = APIRouter(prefix="/players", tags=["Players"])


@router.post("/", response_model=PlayerOut)
def create_player(data: PlayerCreate, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
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
def update_player(player_id: int, data: PlayerUpdate, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(player, field, value)
    db.commit()
    db.refresh(player)
    return player


@router.delete("/{player_id}")
def delete_player(player_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    db.delete(player)
    db.commit()
    return {"detail": "Player deleted"}
