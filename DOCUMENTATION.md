# BOXcric — Project Documentation

## Cricket Match Management & Live Scoring Platform

---

## 1. Problem Definition

### 1.1 Background
In regular/local cricket matches played among friends, clubs, and community teams, there is no affordable or accessible tool to manage match scoring, track player statistics, maintain records, and provide real-time updates. Existing cricket apps like Cricbuzz and ESPNcricinfo cater only to professional tournaments, leaving amateur cricket communities without proper match management infrastructure.

### 1.2 Problem Statement
Design and develop a **web-based cricket match management platform** that enables local cricket communities to:
- Create and manage teams and players
- Conduct ball-by-ball live scoring with real-time updates
- Track comprehensive player statistics, records, and rankings
- Provide a user-facing app for fans to follow matches, view stats, and interact
- Ensure data persistence across deployments

### 1.3 Key Challenges
| Challenge | Description |
|-----------|-------------|
| **Real-time scoring** | Ball-by-ball updates must reflect instantly for all connected users |
| **Data accuracy** | Scoring mistakes happen — need undo/correction mechanism |
| **User engagement** | Fans need interactive features beyond passive viewing |
| **Data persistence** | Free hosting platforms (Render) have ephemeral filesystems |
| **Mobile-first** | Most users access from phones — needs PWA support |
| **Zero cost** | Entire platform must run on free-tier services |

---

## 2. Scope of the Project

### 2.1 In Scope
| Module | Features |
|--------|----------|
| **Match Management** | Create matches, record toss, start/end matches, super overs |
| **Live Scoring** | Ball-by-ball recording with extras, wickets, fielder info |
| **Real-time Updates** | WebSocket-based live score push to all connected clients |
| **Player Management** | Create/edit/delete players with batting/bowling styles |
| **Team Management** | Create teams, assign players, set captain/vice-captain/host |
| **Statistics** | Career batting & bowling stats per player |
| **Records** | All-time records — highest score, best bowling, team totals |
| **Rankings** | Weighted ranking system for batting, bowling, all-rounders |
| **User System** | Registration, OTP login, profile management, photo upload |
| **Notifications** | In-app notifications for match events to involved players |
| **Win Probability** | Live win percentage calculation with multiple factors |
| **Commentary** | Auto-generated ball-by-ball and over-by-over commentary |
| **Social Features** | MOM voting, predictions, emoji reactions, fantasy XI |
| **Video Gallery** | Upload match videos or add YouTube links |
| **Match Photos** | Upload and view match photos |
| **PWA** | Installable web app with offline support for static assets |
| **Admin Panel** | Full CRUD for all entities |

### 2.2 Out of Scope
- Native mobile app (iOS/Android) — PWA covers mobile use
- Payment/subscription system
- Tournament/league management with points tables
- Umpire decision review system
- AI-based shot/delivery classification
- Multi-language support

### 2.3 Target Users
| User Type | Description |
|-----------|-------------|
| **Admin/Scorer** | Creates matches, teams, players; does ball-by-ball scoring |
| **Player** | Registers, views own stats, records, rankings, gets notifications |
| **Fan/Viewer** | Follows live matches, views scores, reacts, predicts, picks fantasy XI |

---

## 3. Plan of Action

### 3.1 Development Phases

```
Phase 1: Core Backend          → Models, APIs for players/teams/matches
Phase 2: Live Scoring           → Ball-by-ball engine, innings management
Phase 3: Frontend               → Admin panel + user-facing app (Jinja2 templates)
Phase 4: Real-time              → WebSocket live score updates
Phase 5: Statistics & Records   → Career stats, all-time records, rankings
Phase 6: User System            → Registration, OTP login, profiles
Phase 7: Advanced Features      → Commentary, win probability, H2H, partnerships
Phase 8: Social Features        → MOM, predictions, reactions, fantasy, milestones
Phase 9: Notifications          → In-app match notifications
Phase 10: Persistence & Deploy  → Turso cloud DB, Render deployment, PWA
```

### 3.2 Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend framework | FastAPI | Async support, auto-docs, WebSocket built-in, Python ecosystem |
| Database (production) | Turso (libsql) | Free tier, SQLite-compatible, cloud-persistent, edge replicas |
| Database (local) | SQLite | Zero-config fallback for development |
| ORM | SQLAlchemy | Mature, supports SQLite/PostgreSQL/Turso, declarative models |
| Auth | JWT + cookies | Stateless, long-lived tokens (365 days), httponly cookies |
| Email | Brevo HTTP API | Free 300 emails/day, no SMTP setup needed |
| Hosting | Render | Free tier, auto-deploy from GitHub, supports Python |
| Frontend | Jinja2 + Vanilla JS | No build step, server-rendered, fast load times |
| PWA | Service worker | Installable, offline static assets, push-to-refresh |

---

## 4. Analysis

### 4.1 System Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Browser    │◄───►│   FastAPI App     │◄───►│   Turso DB  │
│  (PWA/JS)   │     │  (Render)         │     │  (Cloud)    │
└─────┬───────┘     └────────┬─────────┘     └──────┬──────┘
      │                      │                       │
      │  WebSocket           │  libsql embedded      │
      │  /ws/live/{id}       │  replica sync          │
      │                      │                       │
      │  HTTP API            │  SQLAlchemy ORM       │
      │  REST endpoints      │                       │
      │                      │  Brevo Email API ────►│ Email
      │  Static files        │                       │
      │  /static/*           │                       │
      └──────────────────────┘                       │
                                                      │
                             ┌────────────────────────┘
                             │ Data stored permanently
                             │ in Turso cloud database
                             └────────────────────────
```

### 4.2 Data Flow — Live Scoring

```
Admin scores a ball
       │
       ▼
POST /scoring/innings/{id}/ball
       │
       ▼
record_ball() service
  ├── Create Ball record
  ├── Update Innings totals (runs, wickets, overs)
  ├── Check innings completion (all out / overs done / target chased)
  ├── Auto-detect milestones (50, 100, 3W, 5W)
  └── Commit to DB (→ syncs to Turso cloud)
       │
       ▼
WebSocket broadcast to /ws/live/{match_id}
       │
       ▼
All connected clients receive updated score
```

### 4.3 Authentication Flow

```
User enters email
       │
       ▼
POST /api/user/forgot-password
  ├── Find or auto-create user
  ├── Generate 6-digit OTP (5 min expiry)
  └── Send via Brevo email API
       │
       ▼
User enters OTP
       │
       ▼
POST /api/user/verify-otp
  ├── Validate OTP
  ├── Generate JWT token (365 days)
  └── Set httponly cookie "boxcric_token"
       │
       ▼
User is logged in (redirected to profile setup if new)
```

### 4.4 Database Persistence Architecture (Turso)

```
On startup:
  libsql.connect("turso_replica.db", sync_url=turso_url, auth_token=token)
  → Downloads latest data from Turso cloud to local replica
  → conn.sync()

SQLAlchemy engine uses libsql connection wrapper:
  → All reads/writes go through libsql driver
  → On commit(): conn.commit() + conn.sync()
  → Data is pushed to Turso cloud immediately

On redeploy (Render):
  → Local file deleted (ephemeral filesystem)
  → On next startup: sync() pulls all data back from Turso cloud
  → Zero data loss
```

---

## 5. Design

### 5.1 Database Schema (ER Diagram)

```
                    ┌──────────┐
                    │  users   │
                    │──────────│
                    │ id (PK)  │
                    │ name     │
                    │ email    │
                    │ is_admin │
                    │ ...      │
                    └────┬─────┘
                         │ user_id
                    ┌────▼─────┐
                    │ players  │
                    │──────────│
                    │ id (PK)  │
                    │ name     │
                    │ bat/bowl │
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │ team_players (M:N)  │
              │    team_id ──┐      │
              │    player_id─┘      │
              └──────────┬──────────┘
                         │
                    ┌────▼─────┐          ┌───────────┐
                    │  teams   │◄────────►│  matches   │
                    │──────────│ team1_id │───────────│
                    │ id (PK)  │ team2_id │ id (PK)   │
                    │ name     │          │ status    │
                    │ captain  │          │ toss/win  │
                    │ host     │          │ overs     │
                    └──────────┘          └─────┬─────┘
                                                │
                                          ┌─────▼─────┐
                                          │  innings   │
                                          │───────────│
                                          │ id (PK)   │
                                          │ match_id  │
                                          │ runs/wkts │
                                          │ overs     │
                                          └─────┬─────┘
                                                │
                                          ┌─────▼─────┐
                                          │   balls    │
                                          │───────────│
                                          │ id (PK)   │
                                          │ innings_id│
                                          │ batter    │
                                          │ bowler    │
                                          │ runs/extra│
                                          │ wicket    │
                                          └───────────┘

  Related tables: notifications, videos, match_photos,
                  mom_votes, match_predictions, reactions, milestones
```

### 5.2 API Design Principles
- **RESTful** — Standard HTTP methods (GET/POST/PUT/DELETE)
- **Resource-based URLs** — `/players/`, `/teams/{id}`, `/matches/{id}/toss`
- **JSON responses** — Pydantic schemas for validation and serialization
- **Cookie auth** — httponly JWT cookie for session management
- **WebSocket** — `/ws/live/{match_id}` for real-time score updates

### 5.3 Frontend Architecture
- **Two interfaces** — Admin (`/admin/*`) for full control, User (`/app/*`) for read-only + social
- **Server-rendered** — Jinja2 templates with `{% extends "base.html" %}`
- **Client-side data** — Vanilla JS `fetch()` calls to REST APIs
- **Dark/light theme** — CSS variables with `[data-theme="dark"]`, persisted in localStorage
- **PWA** — Service worker caches static assets only (not HTML/API responses)
- **Mobile-first** — Bottom navigation bar, responsive grid, touch gestures

---

## 6. Implementation (with Source Code)

### 6.1 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11.11 |
| Web Framework | FastAPI | 0.135+ |
| ORM | SQLAlchemy | 2.0+ |
| Database | Turso (libsql-experimental) | 0.0.55 |
| Auth | python-jose (JWT) + bcrypt | — |
| Template Engine | Jinja2 | 3.1+ |
| ASGI Server | Uvicorn | — |
| Email | Brevo HTTP API | — |
| Hosting | Render (free tier) | — |
| Version Control | Git + GitHub | — |

### 6.2 Project Structure

```
BOXcric/
├── app/
│   ├── main.py              # FastAPI app, routes, startup, migrations
│   ├── config.py            # Environment config (DATABASE_URL, etc.)
│   ├── database.py          # SQLAlchemy engine + Turso libsql connection
│   ├── auth.py              # JWT, password hashing, OTP, cookie auth
│   ├── models/              # SQLAlchemy table models (14 tables)
│   ├── routers/             # API endpoint handlers (13 routers)
│   ├── schemas/             # Pydantic request/response models
│   ├── services/            # Business logic (scoring, stats, rankings, etc.)
│   └── websocket/           # WebSocket connection manager
├── templates/               # Jinja2 HTML templates (admin + user)
├── static/                  # CSS, JS, icons, uploads, PWA files
├── requirements.txt         # Python dependencies
├── Procfile                 # Render start command
└── runtime.txt              # Python version pin (3.11.11)
```

---

### 6.3 Configuration Module

**`app/config.py`** — Loads environment variables and determines database URL.

```python
import os
from dotenv import load_dotenv
load_dotenv()

_db_url = os.getenv("DATABASE_URL", "")
# Render uses postgres:// but SQLAlchemy needs postgresql://
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
# Ignore empty or invalid DATABASE_URL, use SQLite
if not _db_url or not _db_url.startswith(("sqlite", "postgresql", "mysql", "libsql")):
    DATABASE_URL = "sqlite:///./boxcric.db"
else:
    DATABASE_URL = _db_url
APP_TITLE = "BOXcric"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Manage scores, stats, records & live scores for regular cricket matches"
```

**What it does:**
- Loads `.env` file for local development
- Reads `DATABASE_URL` from environment (set on Render for production)
- Auto-converts `postgres://` to `postgresql://` (Render compatibility)
- Falls back to local SQLite if no valid URL is set
- Supports `sqlite`, `postgresql`, `mysql`, and `libsql` (Turso) URL schemes

---

### 6.4 Database Module — Turso Integration

**`app/database.py`** — Creates SQLAlchemy engine with Turso cloud sync.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from app.config import DATABASE_URL

_is_sqlite = DATABASE_URL.startswith("sqlite")
_is_libsql = DATABASE_URL.startswith("libsql")

if _is_libsql:
    import libsql_experimental as libsql
    from urllib.parse import urlparse, parse_qs

    _parsed = urlparse(DATABASE_URL)
    _turso_url = f"libsql://{_parsed.hostname}"
    _auth_token = parse_qs(_parsed.query).get("authToken", [""])[0]

    class _LibsqlCursorWrapper:
        """Wraps libsql cursor to match sqlite3.Cursor interface for SQLAlchemy."""
        def __init__(self, cursor):
            self._cursor = cursor
            self.description = cursor.description
            self.rowcount = cursor.rowcount
            self.lastrowid = getattr(cursor, 'lastrowid', None)

        def execute(self, sql, params=None):
            if params:
                self._cursor.execute(sql, params)
            else:
                self._cursor.execute(sql)
            self.description = self._cursor.description
            self.rowcount = self._cursor.rowcount
            self.lastrowid = getattr(self._cursor, 'lastrowid', None)
            return self

        def fetchone(self):
            return self._cursor.fetchone()

        def fetchall(self):
            return self._cursor.fetchall()

        def close(self):
            self._cursor.close()

        def __iter__(self):
            return iter(self._cursor)

    class _LibsqlConnectionWrapper:
        """Wraps libsql Connection to be fully compatible with sqlite3.Connection.
        All DB operations go through libsql driver so data syncs to Turso cloud."""
        def __init__(self):
            self._conn = libsql.connect(
                "turso_replica.db", sync_url=_turso_url, auth_token=_auth_token
            )
            self._conn.sync()  # Pull latest data from Turso cloud on startup

        def cursor(self):
            return _LibsqlCursorWrapper(self._conn.cursor())

        def commit(self):
            self._conn.commit()
            self._conn.sync()  # Push changes to Turso cloud after every commit

        def rollback(self):
            self._conn.rollback()

        def execute(self, sql, params=None):
            if params:
                return _LibsqlCursorWrapper(self._conn.execute(sql, params))
            return _LibsqlCursorWrapper(self._conn.execute(sql))

        def create_function(self, *args, **kwargs):
            pass  # Stub — SQLAlchemy pysqlite calls this, libsql doesn't support it

        @property
        def isolation_level(self):
            return ""

        @isolation_level.setter
        def isolation_level(self, val):
            pass

    _shared_conn = _LibsqlConnectionWrapper()

    engine = create_engine(
        "sqlite://",
        creator=lambda: _shared_conn,  # All queries go through libsql connection
        poolclass=StaticPool,           # Single shared connection
    )
```

**What it does:**
- Parses the Turso `libsql://` URL to extract hostname and auth token
- Creates an **embedded replica**: local SQLite file synced with Turso cloud
- `_LibsqlConnectionWrapper` wraps the native libsql connection to match `sqlite3.Connection` API
- On **startup**: `sync()` pulls all data from Turso cloud to local file
- On every **commit**: `commit()` + `sync()` pushes writes to Turso cloud
- SQLAlchemy thinks it's talking to regular SQLite, but all operations go through libsql
- **Result**: Data persists permanently in Turso cloud; survives Render redeploys

---

### 6.5 Authentication Module

**`app/auth.py`** — Handles JWT tokens, password hashing, OTP generation, and email sending.

```python
SECRET_KEY = os.getenv("SECRET_KEY", "boxcric-secret-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8760  # 365 days — stay logged in
OTP_EXPIRE_MINUTES = 5

# In-memory OTP store
_otp_store: dict[str, dict] = {}

def hash_password(password: str) -> str:
    """Hash password using bcrypt with auto-generated salt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    """Compare plain text password against bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(user_id: int, email: str) -> str:
    """Generate JWT token with user ID, email, and 365-day expiry."""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    """Extract user from 'boxcric_token' httponly cookie. Returns None if not logged in."""
    token = request.cookies.get("boxcric_token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user_id = int(payload.get("sub", 0))
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()

def generate_otp(identifier: str, user_id: int) -> str:
    """Generate 6-digit OTP, store in memory with 5-minute expiry."""
    otp = str(random.randint(100000, 999999))
    _otp_store[identifier] = {
        "otp": otp,
        "expires": datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES),
        "user_id": user_id,
    }
    return otp

def send_otp_email(to_email: str, otp: str, user_name: str = "User") -> bool:
    """Send OTP email via Brevo HTTP API. Returns True if sent successfully."""
    # Constructs HTML email with styled OTP display
    # Makes HTTP POST to https://api.brevo.com/v3/smtp/email
    # Returns False if Brevo not configured (logs OTP to console instead)
    ...

def verify_otp(identifier: str, otp: str) -> int | None:
    """Verify OTP. Returns user_id if valid, None if expired/invalid. Consumes OTP on success."""
    entry = _otp_store.get(identifier)
    if not entry or datetime.utcnow() > entry["expires"] or entry["otp"] != otp:
        return None
    user_id = entry["user_id"]
    _otp_store.pop(identifier, None)  # One-time use
    return user_id
```

**What it does:**
- **Password security**: bcrypt hashing with random salt (never stored in plain text)
- **JWT tokens**: Encoded with HS256, 365-day expiry, stored as httponly cookie
- **Cookie auth**: `get_current_user_from_cookie()` extracts user from request cookies — used by all authenticated endpoints
- **OTP system**: 6-digit codes stored in-memory with 5-minute expiry, consumed on verification
- **Email delivery**: Brevo REST API sends styled HTML emails with OTP codes

---

### 6.6 Data Models (SQLAlchemy)

#### 6.6.1 User Model — `app/models/user.py`

```python
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
    photo = Column(String(300), nullable=True)        # Profile photo URL
    age = Column(Integer, nullable=True)
    height = Column(String(10), nullable=True)
    batting_hand = Column(String(20), nullable=True)  # right / left
    bowling_hand = Column(String(20), nullable=True)  # right / left / none
    bowling_type = Column(String(30), nullable=True)  # fast / medium / offspin / etc.
    gender = Column(String(10), nullable=True)
    player_role = Column(String(30), nullable=True)   # batsman / bowler / allrounder / wk_batsman
    profile_complete = Column(Boolean, default=False)
    profile_edits = Column(Integer, default=0)         # Max 5 full edits allowed
    is_admin = Column(Boolean, default=False)
```

**What it does:** Stores registered user accounts with authentication credentials, cricket profile data, and admin status. `profile_edits` limits how many times users can change key fields (batting style, role, etc.).

#### 6.6.2 Player Model — `app/models/player.py`

```python
class BattingStyle(str, enum.Enum):
    RIGHT_HAND = "right_hand"
    LEFT_HAND = "left_hand"

class BowlingStyle(str, enum.Enum):
    RIGHT_ARM_FAST = "right_arm_fast"
    LEFT_ARM_FAST = "left_arm_fast"
    RIGHT_ARM_MEDIUM = "right_arm_medium"
    # ... 8 bowling styles + NONE

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    nickname = Column(String(50), nullable=True)
    batting_style = Column(SQLEnum(BattingStyle), default=BattingStyle.RIGHT_HAND)
    bowling_style = Column(SQLEnum(BowlingStyle), default=BowlingStyle.NONE)
    phone = Column(String(15), nullable=True)
    player_role = Column(String(30), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Links to registered user
```

**What it does:** Represents a cricket player. Linked to a User account via `user_id` — when a user completes their profile, a corresponding Player record is auto-created/synced.

#### 6.6.3 Team Model — `app/models/team.py`

```python
class TeamPlayer(Base):
    """Junction table for many-to-many Team ↔ Player relationship."""
    __tablename__ = "team_players"
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    short_name = Column(String(10), nullable=True)
    captain_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    vice_captain_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=True)      # Scorer permission
    cohost_id = Column(Integer, ForeignKey("users.id"), nullable=True)    # Scorer permission
    players = relationship("Player", secondary="team_players", lazy="joined")
```

**What it does:** Teams have a roster of players (many-to-many via `team_players`), a captain/vice-captain, and host/cohost who have scoring permissions for matches.

#### 6.6.4 Match Model — `app/models/match.py`

```python
class MatchStatus(str, enum.Enum):
    SCHEDULED = "scheduled"   # Match created, awaiting toss
    TOSS = "toss"             # Toss done, innings created
    LIVE = "live"             # Match in progress
    INNINGS_BREAK = "innings_break"
    COMPLETED = "completed"   # Result calculated
    ABANDONED = "abandoned"

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
    toss_decision = Column(SQLEnum(TossDecision), nullable=True)  # bat / bowl
    winner_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    result_summary = Column(String(300), nullable=True)  # "Team A won by 5 runs"
    innings = relationship("Innings", back_populates="match", lazy="joined")
```

**What it does:** Represents a cricket match with lifecycle status tracking. The status progresses: `SCHEDULED → TOSS → LIVE → COMPLETED`. Relationships to teams (playing, toss winner, match winner) and innings.

#### 6.6.5 Innings Model — `app/models/innings.py`

```python
class Innings(Base):
    __tablename__ = "innings"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    innings_number = Column(Integer, nullable=False)  # 1, 2, or 3+ for super overs
    batting_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    bowling_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    total_runs = Column(Integer, default=0)
    total_wickets = Column(Integer, default=0)
    total_overs = Column(Integer, default=0)     # Completed full overs
    total_balls = Column(Integer, default=0)      # Balls bowled in current over (0–5)
    extras = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    balls = relationship("Ball", back_populates="innings", lazy="joined")
```

**What it does:** Stores running totals for each innings. Updated on every ball delivery. `total_overs` + `total_balls` together represent the current over (e.g., 12.4 = 12 overs, 4 balls). Super overs have `innings_number > 2`.

#### 6.6.6 Ball Model — `app/models/ball.py`

```python
class ExtraType(str, enum.Enum):
    NONE = "none"
    WIDE = "wide"
    NO_BALL = "no_ball"
    BYE = "bye"
    LEG_BYE = "leg_bye"

class WicketType(str, enum.Enum):
    BOWLED = "bowled"
    CAUGHT = "caught"
    LBW = "lbw"
    RUN_OUT = "run_out"
    STUMPED = "stumped"
    HIT_WICKET = "hit_wicket"
    RETIRED = "retired"

class Ball(Base):
    __tablename__ = "balls"
    id = Column(Integer, primary_key=True, index=True)
    innings_id = Column(Integer, ForeignKey("innings.id"), nullable=False)
    over_number = Column(Integer, nullable=False)       # 0-indexed
    ball_number = Column(Integer, nullable=False)        # 1–6 within over
    batter_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    bowler_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    non_striker_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    runs_scored = Column(Integer, default=0)             # Runs off the bat
    extra_type = Column(SQLEnum(ExtraType), default=ExtraType.NONE)
    extra_runs = Column(Integer, default=0)
    is_wicket = Column(Boolean, default=False)
    wicket_type = Column(SQLEnum(WicketType), default=WicketType.NONE)
    dismissed_player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    fielder_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    is_legal = Column(Boolean, default=True)             # False for wides/no-balls
    is_correction = Column(Boolean, default=False)        # True = re-scored after undo
```

**What it does:** Records every single delivery in a match. Captures who batted, who bowled, runs scored, extras, wicket details, and fielder involved. `is_legal = False` for wides/no-balls (don't count as a ball faced). `is_correction = True` when a ball was re-scored after undo (prevents further undo).

#### 6.6.7 Notification Model — `app/models/notification.py`

```python
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    type = Column(String(50), nullable=False)    # match_created, toss, match_started, match_ended
    title = Column(String(200), nullable=False)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**What it does:** In-app notifications for match events. Created for every user involved in a match (players + hosts). Users see a bell icon with unread count in the header.

#### 6.6.8 Extra Models — `app/models/extras.py`

```python
class MatchPhoto(Base):     # Photos uploaded per match
class MOMVote(Base):        # Man of the Match votes (one vote per user per match)
class MatchPrediction(Base): # Users predict match winner before/during match
class Reaction(Base):       # Emoji reactions to balls/matches (🔥🎉😱👏)
class Milestone(Base):      # Auto-awarded badges (century, fifty, 5-wicket haul)
```

**What they do:** Social and engagement features — voting for Man of the Match, predicting winners, reacting to exciting moments, and tracking player milestones.

---

### 6.7 Core Service — Scoring Engine

**`app/services/scoring.py`** — The heart of the application. Records ball-by-ball scoring.

```python
def record_ball(db: Session, innings_id: int, data: BallInput) -> Ball:
    """Record a single ball delivery and update innings totals."""
    innings = db.query(Innings).filter(Innings.id == innings_id).first()
    if not innings:
        raise ValueError("Innings not found")
    if innings.is_completed:
        raise ValueError("Innings is already completed")

    match = db.query(Match).filter(Match.id == innings.match_id).first()

    # Determine if this is a legal delivery
    is_legal = data.extra_type not in (ExtraType.WIDE, ExtraType.NO_BALL)

    # Calculate ball/over number
    if is_legal:
        current_ball = innings.total_balls + 1
        over_number = innings.total_overs
        ball_number = current_ball
        if current_ball >= 6:           # Over complete
            innings.total_overs += 1
            innings.total_balls = 0
        else:
            innings.total_balls = current_ball
    else:
        # Wides/no-balls don't count as a legal delivery
        over_number = innings.total_overs
        ball_number = innings.total_balls + 1

    # Create the Ball record
    ball = Ball(
        innings_id=innings_id,
        over_number=over_number, ball_number=ball_number,
        batter_id=data.batter_id, bowler_id=data.bowler_id,
        non_striker_id=data.non_striker_id,
        runs_scored=data.runs_scored,
        extra_type=data.extra_type, extra_runs=data.extra_runs,
        is_wicket=data.is_wicket, wicket_type=data.wicket_type,
        dismissed_player_id=data.dismissed_player_id,
        fielder_id=data.fielder_id,
        is_legal=is_legal,
        is_correction=data.is_correction,
    )
    db.add(ball)

    # Update innings totals
    innings.total_runs += data.runs_scored + data.extra_runs
    innings.extras += data.extra_runs
    if data.is_wicket:
        innings.total_wickets += 1

    # Check if innings should end
    team_size = db.query(TeamPlayer).filter(
        TeamPlayer.team_id == innings.batting_team_id).count()
    max_wickets = max(team_size - 1, 1) if team_size > 0 else 10

    # Super over: 1 over, max 2 wickets
    is_super_over = innings.innings_number > 2
    if is_super_over:
        overs_limit = 1
        max_wickets = min(max_wickets, 2)
    else:
        overs_limit = match.overs

    if innings.total_wickets >= max_wickets or innings.total_overs >= overs_limit:
        innings.is_completed = True

    # Check if target chased (2nd innings)
    if innings.innings_number % 2 == 0:
        prev_inn = db.query(Innings).filter(
            Innings.match_id == innings.match_id,
            Innings.innings_number == innings.innings_number - 1
        ).first()
        if prev_inn and innings.total_runs > prev_inn.total_runs:
            innings.is_completed = True

    db.commit()
    db.refresh(ball)
    return ball
```

**What it does:**
1. Validates the innings exists and is not completed
2. Determines if the delivery is legal (wides/no-balls don't count)
3. Calculates over and ball numbers — auto-increments over when 6 legal balls bowled
4. Creates a detailed `Ball` record with all match data
5. Updates running `Innings` totals (runs, wickets, overs, extras)
6. Auto-detects innings completion: all out, overs finished, or target chased
7. Handles super over rules (1 over max, 2 wickets max)

---

### 6.8 Notification Service

**`app/services/notifications.py`** — Sends notifications to all users involved in a match.

```python
def get_match_user_ids(db: Session, match: Match) -> set[int]:
    """Get all user_ids of players in both teams, plus host/cohost."""
    user_ids = set()
    for team_id in [match.team1_id, match.team2_id]:
        rows = (
            db.query(Player.user_id)
            .join(TeamPlayer, TeamPlayer.player_id == Player.id)
            .filter(TeamPlayer.team_id == team_id, Player.user_id.isnot(None))
            .all()
        )
        for (uid,) in rows:
            user_ids.add(uid)
    # Also include team hosts/cohosts
    from app.models.team import Team
    for team_id in [match.team1_id, match.team2_id]:
        team = db.query(Team).filter(Team.id == team_id).first()
        if team:
            if team.host_id: user_ids.add(team.host_id)
            if team.cohost_id: user_ids.add(team.cohost_id)
    return user_ids

def notify_match_users(db, match, notif_type, title, message):
    """Create a notification for every user involved in the match."""
    for uid in get_match_user_ids(db, match):
        db.add(Notification(user_id=uid, match_id=match.id,
            type=notif_type, title=title, message=message))
    db.commit()
```

**What it does:** Finds all users linked to players in both teams (via `Player.user_id`), plus team hosts/cohosts, and creates a `Notification` record for each. Called when matches are created, toss recorded, match started, or match ended.

---

### 6.9 WebSocket — Live Score Updates

**`app/websocket/live_score.py`** — Manages WebSocket connections for real-time score pushes.

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, match_id: int):
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = []
        self.active_connections[match_id].append(websocket)

    def disconnect(self, websocket: WebSocket, match_id: int):
        if match_id in self.active_connections:
            self.active_connections[match_id].remove(websocket)

    async def broadcast(self, match_id: int, data: dict):
        """Send score update to all clients watching this match."""
        if match_id in self.active_connections:
            for ws in self.active_connections[match_id]:
                try:
                    await ws.send_json(data)
                except:
                    pass

manager = ConnectionManager()
```

**What it does:** Maintains a dictionary of WebSocket connections per match. When a ball is scored, the updated score is broadcast to all connected clients watching that match. Clients connect to `/ws/live/{match_id}`.

---

### 6.10 Match Lifecycle API

**`app/routers/matches.py`** — Manages the full match lifecycle.

```python
@router.post("/")
def create_match(data: MatchCreate, request: Request, db: Session = Depends(get_db)):
    """Create a new match and notify all players in both teams."""
    match = Match(**data.model_dump())
    db.add(match)
    db.commit()
    notify_match_users(db, match, "match_created",
        f"New Match: {t1.name} vs {t2.name}",
        f"You've been selected for {t1.name} vs {t2.name}. Get ready!")
    return match

@router.post("/{match_id}/toss")
def record_toss(match_id, data: MatchToss, ...):
    """Record toss result, create both innings, notify players."""
    match.toss_winner_id = data.toss_winner_id
    match.toss_decision = data.toss_decision
    match.status = MatchStatus.TOSS
    # Create 2 innings based on toss decision (bat first / bowl first)
    db.add_all([innings1, innings2])

@router.post("/{match_id}/start")
def start_match(match_id, ...):
    """Set match status to LIVE and notify players."""
    match.status = MatchStatus.LIVE

@router.post("/{match_id}/end")
def end_match(match_id, ...):
    """Calculate result (runs/wickets won), set winner, notify players."""
    match.status = MatchStatus.COMPLETED
    match.result_summary = f"{winner.name} won by {diff} runs"

@router.post("/{match_id}/super-over")
def start_super_over(match_id, ...):
    """Create 2 new super over innings (1 over each), reset match to LIVE."""
```

**What it does:** Implements the match lifecycle: Create → Toss → Start → End, with optional Super Over for ties. Each state change sends notifications to all involved players.

---

### 6.11 User Authentication API

**`app/routers/user_auth.py`** — Registration, OTP login, profile management.

```python
@router.post("/register")
def register(data: UserRegister, response: Response, db):
    """Register new user, hash password, set JWT cookie."""
    user = User(name=data.name, email=data.email,
                hashed_password=hash_password(data.password))
    db.add(user)
    token = create_access_token(user.id, user.email)
    response.set_cookie(key="boxcric_token", value=token,
        httponly=True, max_age=365*24*3600, samesite="lax")

@router.post("/forgot-password")
def forgot_password(data, db):
    """Send OTP to email. Auto-registers if email not found."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(name="New User", email=email, ...)  # Auto-create
    otp = generate_otp(user.email, user.id)
    send_otp_email(user.email, otp, user.name)

@router.post("/verify-otp")
def verify_otp_endpoint(data, response, db):
    """Verify OTP and log the user in with JWT cookie."""
    user_id = verify_otp(otp_key, data.otp)
    token = create_access_token(user.id, user.email)
    response.set_cookie(key="boxcric_token", value=token, httponly=True)

@router.post("/profile")
def update_profile(data: ProfileUpdate, request, db):
    """Update profile. Key fields (batting hand, role, etc.) limited to 5 edits."""
    if restricted_changed:
        if user.profile_edits >= 5:
            raise HTTPException(400, "Profile edit limit reached (5/5)")
        user.profile_edits += 1
    user.profile_complete = True
    sync_user_to_player(user, db)  # Keep Player record in sync
```

**What it does:**
- **Register**: Creates user, hashes password with bcrypt, sets 365-day JWT cookie
- **OTP Login**: Sends 6-digit OTP via email, auto-creates account if new user
- **Profile**: Updates cricket details with 5-edit limit on key fields; auto-syncs to Player record

---

### 6.12 Undo/Correction System

**`app/routers/features.py`** — One-time ball correction.

```python
@router.delete("/undo/{innings_id}")
def undo_last_ball(innings_id: int, db):
    """Undo the last ball. Each ball position allows only one correction."""
    last_ball = db.query(Ball).filter(Ball.innings_id == innings_id)\
        .order_by(Ball.id.desc()).first()
    if last_ball.is_correction:
        raise HTTPException(400, "This ball was already corrected once.")

    # Reverse the ball's effect on innings
    inn.total_runs -= (last_ball.runs_scored + last_ball.extra_runs)
    inn.extras -= last_ball.extra_runs
    if last_ball.is_wicket:
        inn.total_wickets -= 1
    if last_ball.is_legal:
        if inn.total_balls > 0:
            inn.total_balls -= 1
        else:
            inn.total_overs -= 1
            inn.total_balls = 5
    inn.is_completed = False
    db.delete(last_ball)
    db.commit()
    return {"detail": "Ball undone. Score the correct ball now.", "is_correction": True}
```

**What it does:** Deletes the last scored ball and reverses its effect on innings totals (runs, wickets, overs). The next ball scored is marked `is_correction = True`, preventing further undos at that position. One correction per ball.

---

### 6.13 Service Worker (PWA)

**`static/sw.js`** — Caches only static assets, never HTML or API responses.

```javascript
const CACHE_NAME = 'boxcric-v3';

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET') return;

  const isStaticAsset = url.pathname.startsWith('/static/');
  const isApiOrPage = url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/app') || url.pathname.startsWith('/admin');

  if (isApiOrPage && !isStaticAsset) {
    // Always go to network for pages/API — prevents cross-user session caching
    event.respondWith(fetch(event.request));
    return;
  }
  // Static assets: network-first with cache fallback
  event.respondWith(
    fetch(event.request).then((response) => {
      if (response.ok) {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
      }
      return response;
    }).catch(() => caches.match(event.request))
  );
});
```

**What it does:** Only caches CSS, JS, and image files under `/static/`. HTML pages and API responses are NEVER cached — this prevents the bug where User B would see User A's cached page. Static assets load from cache when offline.

---

## 7. Environment Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./boxcric.db` |
| `SECRET_KEY` | JWT signing key | `boxcric-secret-change-in-production-2026` |
| `BREVO_API_KEY` | Brevo email API key | (empty — OTP logged to console) |
| `BREVO_SENDER_EMAIL` | Brevo sender email | (empty) |
| `RENDER_EXTERNAL_URL` | Render app URL for keep-alive | `https://boxcric.onrender.com` |

### Database URL Formats Supported
```
sqlite:///./boxcric.db                              # Local SQLite (default)
libsql://db-name.aws-us-west-2.turso.io?authToken=… # Turso cloud
postgresql://user:pass@host/db                       # PostgreSQL (Neon, etc.)
```

---

## 8. Deployment

### 8.1 Render Configuration
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Python Version**: `3.11.11` (pinned in `runtime.txt`)
- **Auto-deploy**: Triggered on push to `main` branch

### 8.2 Keep-Alive
A background task pings `/health` every 10 minutes to prevent Render's free-tier from sleeping.

### 8.3 URLs
| URL | Purpose |
|-----|---------|
| `https://boxcric.onrender.com/app` | User-facing app |
| `https://boxcric.onrender.com/admin` | Admin panel |
| `https://boxcric.onrender.com/health` | Health check |
| `https://boxcric.onrender.com/docs` | Auto-generated API docs (Swagger) |

---

## 9. Testing & Verification

### 9.1 Data Persistence Test
1. Create a player via admin panel
2. Kill the server + delete local database file
3. Restart the server
4. Verify the player still exists (synced from Turso cloud)

### 9.2 Key Test Scenarios
| Scenario | Expected Result |
|----------|----------------|
| Create match with 2 teams | Match created, players notified |
| Record toss | Innings created, status → TOSS |
| Score a ball (6 runs) | Ball recorded, innings total updated, WebSocket broadcast |
| Undo last ball | Ball deleted, innings totals reversed, correction flag set |
| End match | Result calculated, notifications sent |
| User registers via OTP | OTP emailed, user created, profile setup |
| Redeploy on Render | All data persists from Turso cloud |

---

## 10. Future Enhancements

| Feature | Description |
|---------|-------------|
| Tournament/League mode | Points table, group stages, knockouts |
| Push notifications | Browser push API for match events |
| Advanced analytics | Wagon wheel, pitch map, scoring zones |
| Multi-language | Hindi, Telugu, etc. |
| Native mobile app | React Native or Flutter wrapper |
| Umpire DRS | Decision review with video replay |
| AI commentary | GPT-powered natural language commentary |

---

*Document generated: March 2026*
*Project: BOXcric — Cricket Match Management Platform*
