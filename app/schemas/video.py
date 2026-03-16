from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VideoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    video_url: str


class VideoOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    video_url: str
    thumbnail: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_by_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
