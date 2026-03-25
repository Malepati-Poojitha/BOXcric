# BOXcric — Complete Project Documentation

> **Cricket Match Management Platform**
> Live scoring, stats, records, rankings & more for regular cricket matches.

**Live URL:** https://boxcric.onrender.com
**Admin Panel:** https://boxcric.onrender.com/admin
**Tech Stack:** FastAPI + SQLAlchemy + Turso (libsql) + Jinja2 + Vanilla JS
**Deployment:** Render (free tier) with self-ping keep-alive

---

## Table of Contents

1. [Architecture](#architecture)
2. [Database Models](#database-models)
3. [API Endpoints](#api-endpoints)
4. [User Pages](#user-pages-app)
5. [Admin Pages](#admin-pages-admin)
6. [Services](#services)
7. [Auth System](#auth-system)
8. [Notifications](#notifications)
9. [WebSocket (Live Score)](#websocket-live-score)
10. [PWA & Frontend](#pwa--frontend)
11. [Database & Deployment](#database--deployment)
12. [Environment Variables](#environment-variables)

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Browser/PWA                    │
│  /app (User Pages)     /admin (Admin Pages)      │
│  WebSocket (/ws/live)  Service Worker (sw.js)    │
└───────────┬─────────────────────┬───────────────┘
            │ HTTP/WS             │
┌───────────▼─────────────────────▼───────────────┐
│              FastAPI Application                  │
│  Routers: players, teams, matches, scoring,      │
│           stats, records, rankings, commentary,   │
│           user_auth, videos, notifications,       │
│           probability, features                   │
│  Services: scoring, stats, records, rankings,    │
│            win_probability, commentary,           │
│            notifications                          │
│  Auth: JWT cookies + OTP email (Brevo)           │
└───────────┬──────────────────────────────────────┘
            │ SQLAlchemy ORM
┌───────────▼──────────────────────────────────────┐
│          Turso (libsql) Cloud Database            │
│   Embedded replica: local file ↔ cloud sync      │
│   All writes go through libsql → synced to cloud │
│   Data persists across redeploys                  │
└──────────────────────────────────────────────────┘
```

---

## Database Models

### users
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary key |
| name | String(100) | Required |
| nickname | String(50) | Optional |
| email | String(200) | Unique, required |
| phone | String(15) | Optional |
| hashed_password | String(200) | bcrypt hash |
| is_active | Boolean | Default true |
| is_admin | Boolean | Default false |
| created_at | DateTime | Auto |
| photo | String(300) | Profile photo path |
| age | Integer | Optional |
| height | String(10) | Optional |
| batting_hand | String(20) | right/left |
| bowling_hand | String(20) | right/left/none |
| bowling_type | String(30) | fast/medium/offspin/legspin/orthodox/chinaman/none |
| gender | String(10) | male/female/other |
| player_role | String(30) | batsman/bowler/allrounder/wk_batsman |
| profile_complete | Boolean | Default false |
| profile_edits | Integer | Max 5 full edits |

### players
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary key |
| name | String(100) | Required |
| nickname | String(50) | Optional |
| batting_style | Enum | right_hand / left_hand |
| bowling_style | Enum | right_arm_fast / left_arm_fast / right_arm_medium / left_arm_medium / right_arm_offspin / left_arm_orthodox / right_arm_legspin / left_arm_chinaman / none |
| phone | String(15) | Optional |
| player_role | String(30) | Optional |
| user_id | Integer | FK → users.id (links registered user to player) |

### teams
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary key |
| name | String(100) | Unique, required |
| short_name | String(10) | e.g. "CSK" |
| captain_id | Integer | FK → players.id |
| vice_captain_id | Integer | FK → players.id |
| host_id | Integer | FK → users.id (can score matches) |
| cohost_id | Integer | FK → users.id (can score matches) |

**team_players** (junction): id, team_id, player_id

### matches
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary key |
| title | String(200) | Optional |
| team1_id / team2_id | Integer | FK → teams.id |
| overs | Integer | Default 20 |
| venue | String(200) | Optional |
| date | DateTime | Match date |
| status | Enum | scheduled / toss / live / innings_break / completed / abandoned |
| toss_winner_id | Integer | FK → teams.id |
| toss_decision | Enum | bat / bowl |
| winner_id | Integer | FK → teams.id |
| result_summary | String(300) | e.g. "Team A won by 5 wickets" |

### innings
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary key |
| match_id | Integer | FK → matches.id |
| innings_number | Integer | 1, 2 (3, 4 for super overs) |
| batting_team_id / bowling_team_id | Integer | FK → teams.id |
| total_runs / total_wickets | Integer | Running totals |
| total_overs / total_balls | Integer | Completed overs + balls in current over |
| extras | Integer | Total extras |
| is_completed | Boolean | Auto-set when all out / overs done / target chased |

### balls
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary key |
| innings_id | Integer | FK → innings.id |
| over_number | Integer | 0-indexed |
| ball_number | Integer | 1-6 within over |
| batter_id / bowler_id / non_striker_id | Integer | FK → players.id |
| runs_scored | Integer | Runs off the bat |
| extra_type | Enum | none / wide / no_ball / bye / leg_bye |
| extra_runs | Integer | Extra runs |
| is_wicket | Boolean | Wicket on this ball? |
| wicket_type | Enum | bowled / caught / lbw / run_out / stumped / hit_wicket / retired |
| dismissed_player_id / fielder_id | Integer | FK → players.id |
| is_legal | Boolean | False for wides/no-balls |
| is_correction | Boolean | True if this ball was re-scored after undo |

### notifications
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary key |
| user_id | Integer | FK → users.id |
| match_id | Integer | FK → matches.id |
| type | String(50) | match_created / toss / match_started / match_ended |
| title / message | String | Notification content |
| is_read | Boolean | Default false |
| created_at | DateTime | Auto |

### Other tables
- **videos**: id, title, description, video_url, thumbnail, uploaded_by, uploaded_by_id, created_at
- **match_photos**: id, match_id, photo_url, caption, uploaded_by, created_at
- **mom_votes**: id, match_id, player_id, voter_id, created_at
- **match_predictions**: id, match_id, user_id, predicted_winner_id, is_correct, created_at
- **reactions**: id, match_id, ball_id, user_id, emoji, created_at
- **milestones**: id, player_id, match_id, badge, title, description, created_at

---

## API Endpoints

### Players `/players`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/players/` | Create player |
| GET | `/players/` | List all players |
| GET | `/players/{id}` | Get player |
| PUT | `/players/{id}` | Update player |
| DELETE | `/players/{id}` | Delete player |

### Teams `/teams`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/teams/` | Create team |
| GET | `/teams/` | List all teams (with players) |
| GET | `/teams/{id}` | Get team |
| PUT | `/teams/{id}` | Update team |
| DELETE | `/teams/{id}` | Delete team |
| POST | `/teams/{id}/players` | Add player to team |
| DELETE | `/teams/{id}/players/{pid}` | Remove player from team |
| POST | `/teams/{id}/captain` | Set captain / vice-captain |
| POST | `/teams/{id}/host` | Set host / co-host (scorer) |

### Matches `/matches`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/matches/` | Create match → notifies all players |
| GET | `/matches/` | List matches (optional `?status=live`) |
| GET | `/matches/{id}` | Get match with innings |
| POST | `/matches/{id}/toss` | Record toss → creates 2 innings |
| POST | `/matches/{id}/start` | Set LIVE → notifies players |
| POST | `/matches/{id}/end` | Calculate result → notifies players |
| POST | `/matches/{id}/super-over` | Create super-over innings |

### Live Scoring `/scoring`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/scoring/innings/{id}/ball` | Record ball (host/co-host only) |
| GET | `/scoring/match/{id}/live` | Live score summary |
| GET | `/scoring/innings/{id}/scorecard` | Full batting + bowling scorecard |
| GET | `/scoring/innings/{id}/lastball` | Last ball state (striker, bowler, dismissed list) |
| GET | `/scoring/match/{id}/graph` | Over-by-over data for charts |

### Stats & Records
| Method | Path | Description |
|--------|------|-------------|
| GET | `/stats/player/{id}` | Full career stats |
| GET | `/records/` | All-time records (7 categories) |
| GET | `/api/rankings/` | Batting, bowling, all-rounder rankings |
| GET | `/api/probability/{id}` | Live win probability |
| GET | `/api/commentary/match/{id}` | Ball-by-ball commentary |

### User Auth `/api/user`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/user/register` | Register → sets auth cookie |
| POST | `/api/user/login` | Login → sets auth cookie |
| POST | `/api/user/logout` | Clear cookie |
| GET | `/api/user/me` | Current user info |
| GET | `/api/user/all` | List all users |
| DELETE | `/api/user/{id}` | Delete user |
| POST | `/api/user/profile` | Update profile (5 edit limit) |
| POST | `/api/user/photo` | Upload profile photo |
| POST | `/api/user/forgot-password` | Send OTP email |
| POST | `/api/user/verify-otp` | Verify OTP → login |
| POST | `/api/user/reset-password` | Reset password with OTP |
| POST | `/api/user/admin/bootstrap` | Make yourself first admin (one-time) |

### Notifications `/api/notifications`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/notifications/` | Get user's notifications |
| POST | `/api/notifications/read-all` | Mark all read |
| POST | `/api/notifications/{id}/read` | Mark one read |

### Features `/api/features`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/features/mom/vote` | Vote Man of the Match |
| GET | `/api/features/mom/{id}` | Get MOM votes |
| POST | `/api/features/predict` | Predict match winner |
| GET | `/api/features/predictions/{id}` | Prediction stats |
| POST | `/api/features/react` | Add emoji reaction |
| DELETE | `/api/features/undo/{id}` | Undo last ball (one-time correction) |
| GET | `/api/features/h2h/{p1}/{p2}` | Head-to-head stats |
| GET | `/api/features/partnerships/{id}` | Batting partnerships |
| GET | `/api/features/milestones` | Player milestones |
| POST | `/api/features/photos/upload` | Upload match photo |
| GET | `/api/features/calendar` | Match schedule calendar |
| POST | `/api/features/fantasy/pick` | Pick fantasy XI |
| GET | `/api/features/fantasy/leaderboard/{id}` | Fantasy leaderboard |

### Videos `/api/videos`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/videos/` | List videos |
| POST | `/api/videos/` | Add video by URL |
| POST | `/api/videos/upload` | Upload video file |
| DELETE | `/api/videos/{id}` | Delete video |

### Other
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| WS | `/ws/live/{match_id}` | WebSocket for live score updates |

---

## User Pages (`/app`)

| Page | Description |
|------|-------------|
| **Home** (`/app`) | Welcome banner, live matches, recent results, upcoming matches, quick stats |
| **Login** (`/app/login`) | OTP-based login (email → OTP → verify), profile setup wizard |
| **Matches** (`/app/matches`) | Match list with filter tabs (All / Live / Upcoming / Completed) |
| **Match Detail** (`/app/match/{id}`) | Live score with WebSocket, scorecard, commentary, win probability, over-by-over graph, reactions, predictions, MOM voting, match photos |
| **Players** (`/app/players`) | Player grid with stats modal, community members section |
| **Records** (`/app/records`) | All-time records cards |
| **Rankings** (`/app/rankings`) | Tabbed rankings with podium + table |
| **Videos** (`/app/videos`) | Video gallery (YouTube embed + uploads) |
| **Profile** (`/app/profile`) | View/edit profile with photo upload, 5-edit limit |

**Common UI**: Notification bell with unread badge + dropdown, dark/light theme toggle, mobile bottom navigation, PWA install banner, pull-to-refresh.

---

## Admin Pages (`/admin`)

| Page | Description |
|------|-------------|
| **Home** (`/admin`) | Admin dashboard |
| **Matches** (`/admin/matches`) | Create / manage all matches |
| **New Match** (`/admin/new-match`) | Create match form |
| **Match Detail** (`/admin/match/{id}`) | Full match control (toss, start, end, super over, undo) |
| **Score** (`/admin/score/{id}`) | Live scoring console (run buttons, extras, wickets, new batter/bowler modals) |
| **Players** (`/admin/players`) | CRUD players |
| **Teams** (`/admin/teams`) | CRUD teams, manage roster, set captain/host |
| **Records** (`/admin/records`) | View records |
| **Rankings** (`/admin/rankings`) | View rankings |
| **Videos** (`/admin/videos`) | Manage videos |
| **Users** (`/admin/users`) | View/delete registered users, see admin status |

---

## Services

| Service | Key Functions |
|---------|---------------|
| **Scoring** | `record_ball()` — updates innings totals, handles extras/wickets, auto-completes innings. `get_live_score()` — run rate, target, required rate. `get_scorecard()` — batting + bowling stats. |
| **Stats** | `get_player_career_stats()` — runs, avg, SR, HS, 50s/100s, wickets, bowling avg, economy |
| **Records** | `get_all_records()` — 7 categories: highest score, best bowling, team totals, career bests |
| **Rankings** | Rating system: batting (runs 40%, avg 25%, SR 15%, boundaries 10%, consistency 10%), bowling (wickets 35%, economy 25%, avg 20%, SR 10%, consistency 10%), all-rounder (average + balance bonus) |
| **Win Probability** | 1st innings: project final score. 2nd innings: chase analysis with CRR vs RRR, wickets, batting depth |
| **Commentary** | Auto-generated ball-by-ball text + over summaries |
| **Notifications** | Find all users in a match (players + hosts) → create notifications on match events |

---

## Auth System

- **Passwords**: bcrypt hashed
- **Tokens**: JWT (HS256), 365-day expiry, stored in `boxcric_token` httponly cookie
- **OTP Login**: 6-digit code, 5-minute expiry, in-memory store, sent via Brevo email API
- **Scorer Authorization**: Only team host/co-host can score matches
- **Admin Bootstrap**: `POST /api/user/admin/bootstrap` — first user to call it becomes admin (only works when no admins exist)

---

## Notifications

Players are notified (in-app) when:
- **Match created** — "You've been selected for Team A vs Team B"
- **Toss done** — "Team A won the toss and chose to bat"
- **Match started** — "Team A vs Team B is now LIVE!"
- **Match ended** — Shows result summary

Notification bell in header shows unread count, polls every 30 seconds.

---

## WebSocket (Live Score)

- **Endpoint**: `ws://host/ws/live/{match_id}`
- Sends initial score on connect
- Keeps alive with ping/pong
- Broadcasts live score updates to all connected clients
- Auto-reconnects after 3 seconds on disconnect

---

## PWA & Frontend

- **Service Worker** (`sw.js`): Network-first for pages/API, cache-first for static assets. Cache version: `boxcric-v3`
- **Manifest**: Standalone mode, portrait orientation, cricket green theme
- **Theme**: Dark/light mode toggle, persisted in localStorage
- **Mobile**: Bottom navigation bar, haptic feedback on scoring, pull-to-refresh
- **Install Banner**: Prompts users to add to home screen

---

## Database & Deployment

### Database (Turso)
- **Type**: libsql (SQLite-compatible, cloud-hosted)
- **Driver**: `libsql-experimental` embedded replica
- **How it works**: Local SQLite file (`turso_replica.db`) synced with Turso cloud. All operations go through `libsql` connection → synced on every commit.
- **Persistence**: Data survives redeploys, restarts, and sleep/wake cycles.
- **Dashboard**: https://turso.tech (database: `boxcric-praneeth`)

### Deployment (Render)
- **Platform**: Render free tier
- **Build**: `pip install -r requirements.txt`
- **Start**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Python**: 3.11.11 (pinned in `runtime.txt`)
- **Keep-alive**: Self-ping every 10 minutes to prevent sleep

### Auto-Migrations
On startup, the app:
1. Creates all tables via `Base.metadata.create_all()`
2. Runs ALTER TABLE migrations for any missing columns
3. Syncs registered users to player records

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes (on Render) | `libsql://your-db.turso.io?authToken=...` |
| `SECRET_KEY` | Recommended | JWT signing key (default: `boxcric-secret-change-in-production-2026`) |
| `BREVO_API_KEY` | For email OTP | Brevo API key (free 300 emails/day) |
| `BREVO_SENDER_EMAIL` | For email OTP | Sender email for OTP emails |
| `RENDER_EXTERNAL_URL` | Auto-set by Render | Used for keep-alive ping |

---

## File Structure

```
BOXcric/
├── Procfile                 # Render start command
├── runtime.txt              # Python version (3.11.11)
├── requirements.txt         # Dependencies
├── app/
│   ├── main.py              # FastAPI app, routes, migrations, keep-alive
│   ├── config.py            # DATABASE_URL, app metadata
│   ├── database.py          # SQLAlchemy engine + Turso wrapper
│   ├── auth.py              # JWT, bcrypt, OTP, admin check
│   ├── models/              # SQLAlchemy models (10 tables)
│   ├── routers/             # API endpoints (13 routers)
│   ├── schemas/             # Pydantic request/response models
│   ├── services/            # Business logic (7 services)
│   └── websocket/           # Live score WebSocket manager
├── templates/
│   ├── base.html            # Admin base template
│   ├── user/                # User-facing pages (10 templates)
│   └── *.html               # Admin pages (10 templates)
└── static/
    ├── manifest.json        # PWA manifest
    ├── sw.js                # Service worker
    ├── css/                 # Styles (dark/light theme)
    ├── js/                  # Frontend JS (API helper, UI components)
    ├── icons/               # PWA icons
    └── uploads/             # User photos, match photos, videos
```
