import os
import asyncio
import urllib.request
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import APP_TITLE, APP_VERSION, APP_DESCRIPTION
from app.database import engine, Base, get_db, SessionLocal
from app.routers import players, teams, matches, scoring, stats, records
from app.routers import user_auth, videos, rankings, probability, commentary, features
from app.routers import notifications
from app.websocket.live_score import manager
from app.services.scoring import get_live_score
from app.auth import get_current_user_from_cookie
from app.models.user import User  # ensure table is created
from app.models.player import Player
from app.models.notification import Notification  # ensure table is created

# Create all tables
Base.metadata.create_all(bind=engine)

# Migrate: add missing columns
try:
    from sqlalchemy import inspect, text
    insp = inspect(engine)

    # Add user_id to players
    if "players" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("players")]
        if "user_id" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE players ADD COLUMN user_id INTEGER"))
            print("[MIGRATE] Added user_id column to players table")
        if "player_role" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE players ADD COLUMN player_role VARCHAR(30)"))
            print("[MIGRATE] Added player_role column to players table")

    # Add captain_id and vice_captain_id to teams
    if "teams" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("teams")]
        if "captain_id" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE teams ADD COLUMN captain_id INTEGER"))
            print("[MIGRATE] Added captain_id column to teams table")
        if "vice_captain_id" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE teams ADD COLUMN vice_captain_id INTEGER"))
            print("[MIGRATE] Added vice_captain_id column to teams table")
        if "host_id" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE teams ADD COLUMN host_id INTEGER"))
            print("[MIGRATE] Added host_id column to teams table")
        if "cohost_id" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE teams ADD COLUMN cohost_id INTEGER"))
            print("[MIGRATE] Added cohost_id column to teams table")

    # Add is_correction to balls
    if "balls" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("balls")]
        if "is_correction" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE balls ADD COLUMN is_correction BOOLEAN DEFAULT 0"))
            print("[MIGRATE] Added is_correction column to balls table")

except Exception as e:
    print(f"[MIGRATE] Warning: {e}")

# Sync existing users with completed profiles to players
try:
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
except Exception as e:
    print(f"[SYNC] Warning: {e}")

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)


# ── Keep-alive: self-ping every 10 min so Render doesn't sleep ──
_keep_alive_task = None

async def _keep_alive():
    """Ping our own /health endpoint every 10 minutes to stay warm."""
    render_url = os.getenv("RENDER_EXTERNAL_URL", "https://boxcric.onrender.com")
    health_url = f"{render_url}/health"
    print(f"[KEEP-ALIVE] Will ping {health_url} every 10 min")
    while True:
        await asyncio.sleep(600)  # 10 minutes
        try:
            req = urllib.request.Request(health_url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp.read()
            print("[KEEP-ALIVE] Ping OK")
        except Exception as e:
            print(f"[KEEP-ALIVE] Ping failed: {e}")

@app.on_event("startup")
async def startup_keep_alive():
    global _keep_alive_task
    _keep_alive_task = asyncio.create_task(_keep_alive())

@app.on_event("shutdown")
async def shutdown_keep_alive():
    global _keep_alive_task
    if _keep_alive_task:
        _keep_alive_task.cancel()


@app.get("/health")
def health_check():
    return {"status": "ok"}


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
app.include_router(notifications.router)


# ===== ADMIN Pages (full control) =====
@app.get("/admin", include_in_schema=False)
def admin_home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"active": "home"})


@app.get("/admin/matches", include_in_schema=False)
def admin_matches(request: Request):
    return templates.TemplateResponse(request, "matches.html", {"active": "matches"})


@app.get("/admin/match/{match_id}", include_in_schema=False)
def admin_match_detail(request: Request, match_id: int):
    return templates.TemplateResponse(request, "match_detail.html", {"active": "matches", "match_id": match_id})


@app.get("/admin/score/{match_id}", include_in_schema=False)
def admin_score(request: Request, match_id: int):
    return templates.TemplateResponse(request, "score.html", {"active": "matches", "match_id": match_id})


@app.get("/admin/new-match", include_in_schema=False)
def admin_new_match(request: Request):
    return templates.TemplateResponse(request, "new_match.html", {"active": "matches"})


@app.get("/admin/players", include_in_schema=False)
def admin_players(request: Request):
    return templates.TemplateResponse(request, "players.html", {"active": "players"})


@app.get("/admin/teams", include_in_schema=False)
def admin_teams(request: Request):
    return templates.TemplateResponse(request, "teams.html", {"active": "teams"})


@app.get("/admin/records", include_in_schema=False)
def admin_records(request: Request):
    return templates.TemplateResponse(request, "records.html", {"active": "records"})


@app.get("/admin/videos", include_in_schema=False)
def admin_videos(request: Request):
    return templates.TemplateResponse(request, "videos.html", {"active": "videos"})


@app.get("/admin/rankings", include_in_schema=False)
def admin_rankings(request: Request):
    return templates.TemplateResponse(request, "rankings.html", {"active": "rankings"})


@app.get("/admin/users", include_in_schema=False)
def admin_users(request: Request):
    return templates.TemplateResponse(request, "users.html", {"active": "users"})


# ===== USER Pages (read-only, with login) =====
def _user_ctx(request: Request, db: Session, active: str, **extra):
    """Build template context for user pages with auth info."""
    from fastapi.responses import RedirectResponse
    user = get_current_user_from_cookie(request, db)
    # If cookie exists but user not found (deleted DB), clear the stale cookie
    token = request.cookies.get("boxcric_token")
    if token and not user:
        response = RedirectResponse(url="/app/login")
        response.delete_cookie("boxcric_token")
        return response
    return {"active": active, "user": user, **extra}


@app.get("/", include_in_schema=False)
def root_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/app")


@app.get("/app", include_in_schema=False)
def user_home(request: Request, db: Session = Depends(get_db)):
    ctx = _user_ctx(request, db, "home")
    if hasattr(ctx, 'status_code'):
        return ctx  # It's a redirect response (stale cookie)
    user = ctx.get("user")
    # If logged in but profile incomplete, redirect to login (profile setup)
    if user and not user.profile_complete:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/app/login")
    return templates.TemplateResponse(request, "user/home.html", ctx)


@app.get("/app/login", include_in_schema=False)
def user_login(request: Request, db: Session = Depends(get_db)):
    from fastapi.responses import RedirectResponse
    user = get_current_user_from_cookie(request, db)
    # Stale cookie — user deleted from DB
    token = request.cookies.get("boxcric_token")
    if token and not user:
        response = RedirectResponse(url="/app/login")
        response.delete_cookie("boxcric_token")
        return response
    # Switch account — clear cookie and show login
    if request.query_params.get("switch"):
        response = RedirectResponse(url="/app/login")
        response.delete_cookie("boxcric_token")
        return response
    # Already logged in with complete profile — go to home
    if user and user.profile_complete:
        return RedirectResponse(url="/app")
    # Logged in but profile incomplete — stay on login page (shows profile setup)
    return templates.TemplateResponse(request, "user/login.html", {"active": "login", "user": user})


@app.get("/app/matches", include_in_schema=False)
def user_matches(request: Request, db: Session = Depends(get_db)):
    ctx = _user_ctx(request, db, "matches")
    if hasattr(ctx, 'status_code'): return ctx
    return templates.TemplateResponse(request, "user/matches.html", ctx)


@app.get("/app/match/{match_id}", include_in_schema=False)
def user_match_detail(request: Request, match_id: int, db: Session = Depends(get_db)):
    ctx = _user_ctx(request, db, "matches", match_id=match_id)
    if hasattr(ctx, 'status_code'): return ctx
    return templates.TemplateResponse(request, "user/match_detail.html", ctx)


@app.get("/app/players", include_in_schema=False)
def user_players(request: Request, db: Session = Depends(get_db)):
    ctx = _user_ctx(request, db, "players")
    if hasattr(ctx, 'status_code'): return ctx
    return templates.TemplateResponse(request, "user/players.html", ctx)


@app.get("/app/records", include_in_schema=False)
def user_records(request: Request, db: Session = Depends(get_db)):
    ctx = _user_ctx(request, db, "records")
    if hasattr(ctx, 'status_code'): return ctx
    return templates.TemplateResponse(request, "user/records.html", ctx)


@app.get("/app/videos", include_in_schema=False)
def user_videos(request: Request, db: Session = Depends(get_db)):
    ctx = _user_ctx(request, db, "videos")
    if hasattr(ctx, 'status_code'): return ctx
    return templates.TemplateResponse(request, "user/videos.html", ctx)


@app.get("/app/rankings", include_in_schema=False)
def user_rankings(request: Request, db: Session = Depends(get_db)):
    ctx = _user_ctx(request, db, "rankings")
    if hasattr(ctx, 'status_code'): return ctx
    return templates.TemplateResponse(request, "user/rankings.html", ctx)


@app.get("/app/profile", include_in_schema=False)
def user_profile(request: Request, db: Session = Depends(get_db)):
    ctx = _user_ctx(request, db, "profile")
    if hasattr(ctx, 'status_code'):
        return ctx
    if not ctx.get("user"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/app/login")
    return templates.TemplateResponse(request, "user/profile.html", ctx)


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
