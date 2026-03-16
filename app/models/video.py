from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base
from datetime import datetime


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=False)       # file path or YouTube/external URL
    thumbnail = Column(String(500), nullable=True)
    uploaded_by = Column(String(100), nullable=True)       # user name or "admin"
    uploaded_by_id = Column(Integer, nullable=True)        # user id (null for admin)
    created_at = Column(DateTime, default=datetime.utcnow)
