from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.commentary import get_match_commentary, get_over_summary

router = APIRouter(prefix="/api/commentary", tags=["Commentary"])


@router.get("/match/{match_id}")
def match_commentary(match_id: int, innings: int = None, limit: int = 50, db: Session = Depends(get_db)):
    """Get ball-by-ball commentary for a match."""
    return get_match_commentary(db, match_id, innings_number=innings, limit=limit)


@router.get("/overs/{innings_id}")
def over_summary(innings_id: int, db: Session = Depends(get_db)):
    """Get over-by-over summary with commentary."""
    return get_over_summary(db, innings_id)
