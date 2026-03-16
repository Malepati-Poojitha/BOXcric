from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
import uuid

from app.database import get_db
from app.models.video import Video
from app.schemas.video import VideoCreate, VideoOut
from app.auth import get_current_user_from_cookie

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads", "videos")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/api/videos", tags=["Videos"])


@router.get("/", response_model=List[VideoOut])
def list_videos(db: Session = Depends(get_db)):
    return db.query(Video).order_by(Video.created_at.desc()).all()


@router.get("/{video_id}", response_model=VideoOut)
def get_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.post("/", response_model=VideoOut)
def add_video_url(data: VideoCreate, request: Request, db: Session = Depends(get_db)):
    """Add a video by URL (YouTube, etc). Both admin and logged-in users can use this."""
    user = get_current_user_from_cookie(request, db)
    uploaded_by = user.name if user else "Admin"
    uploaded_by_id = user.id if user else None

    if not data.title or not data.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    if not data.video_url or not data.video_url.strip():
        raise HTTPException(status_code=400, detail="Video URL is required")

    video = Video(
        title=data.title.strip(),
        description=data.description,
        video_url=data.video_url.strip(),
        uploaded_by=uploaded_by,
        uploaded_by_id=uploaded_by_id,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.post("/upload", response_model=VideoOut)
async def upload_video_file(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a video file. Both admin and logged-in users can use this."""
    user = get_current_user_from_cookie(request, db)
    uploaded_by = user.name if user else "Admin"
    uploaded_by_id = user.id if user else None

    allowed = ["video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"]
    if video.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only MP4, WebM, MOV, AVI allowed")

    contents = await video.read()
    if len(contents) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Video must be under 100MB")

    ext = video.filename.rsplit(".", 1)[-1] if "." in video.filename else "mp4"
    filename = f"{uuid.uuid4().hex[:12]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    vid = Video(
        title=title.strip(),
        description=description,
        video_url=f"/static/uploads/videos/{filename}",
        uploaded_by=uploaded_by,
        uploaded_by_id=uploaded_by_id,
    )
    db.add(vid)
    db.commit()
    db.refresh(vid)
    return vid


@router.delete("/{video_id}")
def delete_video(video_id: int, db: Session = Depends(get_db)):
    """Delete a video (admin only)."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Delete file if it's a local upload
    if video.video_url and video.video_url.startswith("/static/uploads/"):
        filepath = os.path.join(BASE_DIR, video.video_url.lstrip("/"))
        if os.path.exists(filepath):
            os.remove(filepath)

    db.delete(video)
    db.commit()
    return {"detail": "Video deleted"}
