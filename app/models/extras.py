from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class MatchPhoto(Base):
    __tablename__ = "match_photos"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    photo_url = Column(String(500), nullable=False)
    caption = Column(String(300), nullable=True)
    uploaded_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MOMVote(Base):
    __tablename__ = "mom_votes"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    voter_id = Column(Integer, nullable=True)  # user id who voted
    created_at = Column(DateTime, default=datetime.utcnow)


class MatchPrediction(Base):
    __tablename__ = "match_predictions"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    predicted_winner_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    is_correct = Column(Boolean, nullable=True)  # set after match ends
    created_at = Column(DateTime, default=datetime.utcnow)


class Reaction(Base):
    __tablename__ = "reactions"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    ball_id = Column(Integer, ForeignKey("balls.id"), nullable=True)
    user_id = Column(Integer, nullable=True)
    emoji = Column(String(10), nullable=False)  # 🔥🎉😱👏
    created_at = Column(DateTime, default=datetime.utcnow)


class Milestone(Base):
    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    badge = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
