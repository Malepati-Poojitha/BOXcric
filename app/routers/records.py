from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.score import RecordOut
from app.services.records import get_all_records

router = APIRouter(prefix="/records", tags=["Records"])


@router.get("/", response_model=List[RecordOut])
def all_records(db: Session = Depends(get_db)):
    """Get all-time records across all completed matches."""
    return get_all_records(db)
