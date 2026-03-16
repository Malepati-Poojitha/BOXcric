from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.win_probability import get_win_probability

router = APIRouter(prefix="/api/probability", tags=["Win Probability"])


@router.get("/{match_id}")
def win_probability(match_id: int, db: Session = Depends(get_db)):
    """Get live win probability with analysis factors."""
    return get_win_probability(db, match_id)
