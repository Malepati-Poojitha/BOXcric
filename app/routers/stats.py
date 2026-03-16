from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.score import PlayerCareerStats
from app.services.stats import get_player_career_stats

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/player/{player_id}", response_model=PlayerCareerStats)
def player_stats(player_id: int, db: Session = Depends(get_db)):
    """Get full career stats for a player."""
    try:
        return get_player_career_stats(db, player_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
