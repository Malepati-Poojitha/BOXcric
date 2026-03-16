import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import APP_TITLE, APP_VERSION, APP_DESCRIPTION
from app.database import engine, Base, get_db, SessionLocal
from app.routers import players, teams, matches, scoring, stats, records
from app.routers import user_auth, videos, rankings, probability, commentary, features
from app.websocket.live_score import manager
from app.services.scoring import get_live_score
from app.auth import get_current_user_from_cookie
from app.models.user import User  # ensure table is created
from app.models.player import Player

# Create all tables
Base.metadata.create_all(bind=engine)

# Migrate: add user_id column to players table if missing
from sqlalchemy import inspect, text
insp = inspect(engine)
if "players" in insp.get_table_names():
    cols = [c["name"] for c in insp.get_columns("players")]
    if "user_id" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE players ADD COLUMN user_id INTEGER REFERENCES users(id)"))

# Sync existing users with completed profiles to players
def _sync_existing_users():
    from app.routers.user_auth import sync_user_to_player
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.profile_complete == True).all()
        for u in users:
            existing = db.query(Player).filter(Player.user_id == u.id).first()
            if not existing:
                sync_user_to_player(u, db)
    finally:
        db.close()

_sync_existing_users()

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)

# Static files & templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Register API routers
app.include_router(players.router)
app.include_router(teams.router)
app.include_router(matches.router)
app.include_router(scoring.router)
app.include_router(stats.router)
app.include_router(records.router)
app.include_router(user_auth.router)
app.include_router(videos.router)
app.include_router(rankings.router)
app.include_router(probability.router)
app.include_router(commentary.router)
app.include_router(features.router)


# ===== ADMIN Pages (full control) =====
@app.get("/admin", include_in_schema=False)
def admin_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "active": "home"})


@app.get("/admin/matches", include_in_schema=False)
def admin_matches(request: Request):
    return templates.TemplateResponse("matches.html", {"request": request, "active": "matches"})


@app.get("/admin/match/{match_id}", include_in_schema=False)
def admin_match_detail(request: Request, match_id: int):
    return templates.TemplateResponse("match_detail.html", {"request": request, "active": "matches", "match_id": match_id})


@app.get("/admin/score/{match_id}", include_in_schema=False)
def admin_score(request: Request, match_id: int):
    return templates.TemplateResponse("score.html", {"request": request, "active": "matches", "match_id": match_id})


@app.get("/admin/new-match", include_in_schema=False)
def admin_new_match(request: Request):
    return templates.TemplateResponse("new_match.html", {"request": request, "active": "matches"})


@app.get("/admin/players", include_in_schema=False)
def admin_players(request: Request):
    return templates.TemplateResponse("players.html", {"request": request, "active": "players"})


@app.get("/admin/teams", include_in_schema=False)
def admin_teams(request: Request):
    return templates.TemplateResponse("teams.html", {"request": request, "active": "teams"})


@app.get("/admin/records", include_in_schema=False)
def admin_records(request: Request):
    return templates.TemplateResponse("records.html", {"request": request, "active": "records"})


@app.get("/admin/videos", include_in_schema=False)
def admin_videos(request: Request):
    return templates.TemplateResponse("videos.html", {"request": request, "active": "videos"})


@app.get("/admin/rankings", include_in_schema=False)
def admin_rankings(request: Request):
    return templates.TemplateResponse("rankings.html", {"request": request, "active": "rankings"})


@app.get("/admin/users", include_in_schema=False)
def admin_users(request: Request):
    return templates.TemplateResponse("users.html", {"request": request, "active": "users"})


# ===== USER Pages (read-only, with login) =====
def _user_ctx(request: Request, db: Session, active: str, **extra):
    """Build template context for user pages with auth info."""
    user = get_current_user_from_cookie(request, db)
    return {"request": request, "active": active, "user": user, **extra}


@app.get("/", include_in_schema=False)
def root_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/app")


@app.get("/app", include_in_schema=False)
def user_home(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("user/home.html", _user_ctx(request, db, "home"))


@app.get("/app/login", include_in_schema=False)
def user_login(request: Request, db: Session = Depends(get_db)):
    # If already logged in, go to home
    user = get_current_user_from_cookie(request, db)
    if user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/app")
    return templates.TemplateResponse("user/login.html", {"request": request, "active": "login", "user": None})


@app.get("/app/matches", include_in_schema=False)
def user_matches(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("user/matches.html", _user_ctx(request, db, "matches"))


@app.get("/app/match/{match_id}", include_in_schema=False)
def user_match_detail(request: Request, match_id: int, db: Session = Depends(get_db)):
    return templates.TemplateResponse("user/match_detail.html", _user_ctx(request, db, "matches", match_id=match_id))


@app.get("/app/players", include_in_schema=False)
def user_players(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("user/players.html", _user_ctx(request, db, "players"))


@app.get("/app/records", include_in_schema=False)
def user_records(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("user/records.html", _user_ctx(request, db, "records"))


@app.get("/app/videos", include_in_schema=False)
def user_videos(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("user/videos.html", _user_ctx(request, db, "videos"))


@app.get("/app/rankings", include_in_schema=False)
def user_rankings(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("user/rankings.html", _user_ctx(request, db, "rankings"))


@app.get("/app/profile", include_in_schema=False)
def user_profile(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("user/profile.html", _user_ctx(request, db, "profile"))


# ===== PWA: Serve service worker from root scope =====
from fastapi.responses import FileResponse

@app.get("/sw.js", include_in_schema=False)
def service_worker():
    return FileResponse(
        os.path.join(BASE_DIR, "static", "sw.js"),
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"}
    )


@app.websocket("/ws/live/{match_id}")
async def websocket_live_score(websocket: WebSocket, match_id: int):
    """WebSocket endpoint for real-time live score updates.
    Connect to ws://host/ws/live/{match_id} to receive live score pushes.
    """
    await manager.connect(websocket, match_id)
    try:
        # Send initial score on connect
        db = next(get_db())
        try:
            score = get_live_score(db, match_id)
            await websocket.send_json(score.model_dump())
        except ValueError:
            await websocket.send_json({"error": "No score data yet"})
        finally:
            db.close()

        # Keep connection alive, listen for pings
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, match_id)
