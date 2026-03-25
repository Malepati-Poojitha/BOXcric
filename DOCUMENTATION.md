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

## 6. Implementation

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
│   ├── __init__.py
│   ├── main.py              # FastAPI app, routes, startup
│   ├── config.py            # Environment config (DATABASE_URL, etc.)
│   ├── database.py          # SQLAlchemy engine + Turso connection
│   ├── auth.py              # JWT, password hashing, OTP, cookie auth
│   ├── models/              # SQLAlchemy table models
│   │   ├── user.py          # User table
│   │   ├── player.py        # Player table
│   │   ├── team.py          # Team + TeamPlayer tables
│   │   ├── match.py         # Match table with status enum
│   │   ├── innings.py       # Innings table
│   │   ├── ball.py          # Ball-by-ball table
│   │   ├── video.py         # Video table
│   │   ├── notification.py  # Notification table
│   │   └── extras.py        # MatchPhoto, MOMVote, Prediction, Reaction, Milestone
│   ├── routers/             # API endpoint handlers
│   │   ├── players.py       # CRUD for players
│   │   ├── teams.py         # CRUD for teams + player assignment
│   │   ├── matches.py       # Match lifecycle (create → toss → start → end)
│   │   ├── scoring.py       # Ball recording + live score + scorecard
│   │   ├── stats.py         # Player career statistics
│   │   ├── records.py       # All-time records
│   │   ├── rankings.py      # Weighted ranking system
│   │   ├── probability.py   # Live win probability engine
│   │   ├── commentary.py    # Ball-by-ball commentary generator
│   │   ├── user_auth.py     # Registration, login, OTP, profile
│   │   ├── videos.py        # Video upload + URL management
│   │   ├── features.py      # MOM, predictions, reactions, H2H, etc.
│   │   └── notifications.py # Notification CRUD
│   ├── schemas/             # Pydantic request/response models
│   │   ├── player.py, team.py, match.py, score.py, user.py, video.py
│   ├── services/            # Business logic
│   │   ├── scoring.py       # record_ball(), get_live_score(), get_scorecard()
│   │   ├── stats.py         # Career stats calculation
│   │   ├── records.py       # All-time record queries
│   │   ├── rankings.py      # Weighted ranking algorithm
│   │   ├── win_probability.py # Probability engine
│   │   ├── commentary.py    # Commentary text generator
│   │   └── notifications.py # Send notifications to match participants
│   └── websocket/
│       └── live_score.py    # WebSocket connection manager
├── templates/               # Jinja2 HTML templates
│   ├── base.html            # Admin layout
│   ├── index.html           # Admin dashboard
│   ├── matches.html         # Admin match list
│   ├── match_detail.html    # Admin match detail + scorecard
│   ├── score.html           # Live scoring console
│   ├── new_match.html       # Create match form
│   ├── players.html         # Admin player management
│   ├── teams.html           # Admin team management
│   ├── records.html, rankings.html, videos.html, users.html
│   └── user/                # User-facing templates
│       ├── base.html        # User layout (header, nav, notification bell)
│       ├── home.html        # Home with live/recent/upcoming matches
│       ├── login.html       # OTP login + registration + profile setup
│       ├── profile.html     # Profile editor
│       ├── matches.html, match_detail.html, players.html
│       ├── records.html, rankings.html, videos.html
├── static/
│   ├── css/style.css        # Full UI stylesheet (dark/light theme)
│   ├── js/app.js            # Shared JS (API helper, toast, theme, PWA)
│   ├── manifest.json        # PWA manifest
│   ├── sw.js                # Service worker (cache static assets only)
│   ├── icons/, images/      # App icons and images
│   └── uploads/             # User-uploaded photos and videos
├── requirements.txt         # Python dependencies
├── Procfile                 # Render start command
├── runtime.txt              # Python version (3.11.11)
└── .env.example             # Environment variable template
```

### 6.3 Key Implementation Details

#### 6.3.1 Turso Database Integration
The app uses **Turso embedded replicas** for database persistence:
- A `libsql` connection creates a local SQLite file (`turso_replica.db`) synced with the Turso cloud
- A custom `_LibsqlConnectionWrapper` class wraps the libsql connection to be compatible with SQLAlchemy's `sqlite3.Connection` interface
- On every `commit()`, data is synced to Turso cloud via `conn.sync()`
- On startup, `conn.sync()` pulls all data from cloud → local replica
- This ensures data survives Render's ephemeral filesystem

#### 6.3.2 Scoring Engine
The `record_ball()` function in `services/scoring.py`:
1. Validates the delivery (legal vs illegal)
2. Calculates over/ball numbers
3. Creates a `Ball` record with all metadata
4. Updates `Innings` totals (runs, wickets, overs, extras)
5. Checks innings completion conditions:
   - All out (wickets ≥ team_size - 1)
   - Overs completed
   - Target chased (2nd innings)
   - Super over limits (1 over, 2 wickets max)
6. Supports undo/correction (one-time per ball via `is_correction` flag)

#### 6.3.3 Rankings Algorithm
Weighted rating system:
- **Batting**: Runs (40%) + Average (25%) + Strike Rate (15%) + Boundaries (10%) + Consistency (10%)
- **Bowling**: Wickets (35%) + Economy (25%) + Average (20%) + Strike Rate (10%) + Consistency (10%)
- **All-rounder**: Combined batting + bowling rating (balanced weights)

#### 6.3.4 Win Probability Engine
Factors considered:
- Current run rate vs required run rate
- Wickets remaining
- Batting team's strength (historical average)
- Tailender detection
- Set batsman bonus
- Overs remaining

#### 6.3.5 Notification System
- Notifications created for all users linked to players in a match (via `Player.user_id`) plus team hosts/cohosts
- Triggered on: match creation, toss, match start, match end
- UI: Bell icon in header with unread badge, dropdown panel, 30-second polling

#### 6.3.6 PWA Implementation
- Service worker (`sw.js`): Network-first strategy, only caches `/static/*` assets (never HTML/API)
- Manifest with app name, icons, theme color
- Install banner prompt
- Pull-to-refresh gesture
- Cache version (`boxcric-v3`) for cache busting

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
