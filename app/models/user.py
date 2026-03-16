from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    nickname = Column(String(50), nullable=True)
    email = Column(String(200), nullable=False, unique=True, index=True)
    phone = Column(String(15), nullable=True)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Profile fields
    photo = Column(String(300), nullable=True)
    age = Column(Integer, nullable=True)
    height = Column(String(10), nullable=True)
    batting_hand = Column(String(20), nullable=True)   # right / left
    bowling_hand = Column(String(20), nullable=True)   # right / left / none
    bowling_type = Column(String(30), nullable=True)   # fast / medium / offspin / legspin / orthodox / chinaman / none
    gender = Column(String(10), nullable=True)           # male / female / other
    player_role = Column(String(30), nullable=True)       # batsman / bowler / allrounder / wk_batsman
    profile_complete = Column(Boolean, default=False)
    profile_edits = Column(Integer, default=0)             # max 5 full edits allowed
