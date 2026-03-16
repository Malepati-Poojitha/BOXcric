from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.rankings import get_all_rankings

router = APIRouter(prefix="/api/rankings", tags=["Rankings"])


@router.get("/")
def rankings(db: Session = Depends(get_db)):
    """Get batting, bowling, and all-rounder rankings."""
    return get_all_rankings(db)
