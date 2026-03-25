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
    from sqlalchemy import text
    # Use raw SQL for everything to avoid FK constraint issues with libsql/Turso
    db.execute(text("DELETE FROM team_players WHERE player_id = :pid"), {"pid": player_id})
    db.execute(text("UPDATE teams SET captain_id = NULL WHERE captain_id = :pid"), {"pid": player_id})
    db.execute(text("UPDATE teams SET vice_captain_id = NULL WHERE vice_captain_id = :pid"), {"pid": player_id})
    db.execute(text("DELETE FROM mom_votes WHERE player_id = :pid"), {"pid": player_id})
    db.execute(text("DELETE FROM milestones WHERE player_id = :pid"), {"pid": player_id})
    db.execute(text("UPDATE balls SET batter_id = NULL WHERE batter_id = :pid"), {"pid": player_id})
    db.execute(text("UPDATE balls SET bowler_id = NULL WHERE bowler_id = :pid"), {"pid": player_id})
    db.execute(text("UPDATE balls SET non_striker_id = NULL WHERE non_striker_id = :pid"), {"pid": player_id})
    db.execute(text("UPDATE balls SET dismissed_player_id = NULL WHERE dismissed_player_id = :pid"), {"pid": player_id})
    db.execute(text("UPDATE balls SET fielder_id = NULL WHERE fielder_id = :pid"), {"pid": player_id})
    db.execute(text("DELETE FROM players WHERE id = :pid"), {"pid": player_id})
    db.commit()
    return {"detail": "Player deleted"}
