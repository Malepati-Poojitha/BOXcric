from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum


class MatchStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    TOSS = "toss"
    LIVE = "live"
    INNINGS_BREAK = "innings_break"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class TossDecision(str, enum.Enum):
    BAT = "bat"
    BOWL = "bowl"


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=True)
    team1_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    team2_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    overs = Column(Integer, nullable=False, default=20)
    venue = Column(String(200), nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.SCHEDULED)
    toss_winner_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    toss_decision = Column(SQLEnum(TossDecision), nullable=True)
    winner_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    result_summary = Column(String(300), nullable=True)

    team1 = relationship("Team", foreign_keys=[team1_id], lazy="joined")
    team2 = relationship("Team", foreign_keys=[team2_id], lazy="joined")
    toss_winner = relationship("Team", foreign_keys=[toss_winner_id])
    winner = relationship("Team", foreign_keys=[winner_id])
    innings = relationship("Innings", back_populates="match", lazy="joined")
