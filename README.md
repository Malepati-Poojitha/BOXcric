# BOXcric 🏏

Cricket match management system for your regular box/gully cricket matches. Track scores, stats, records, and stream live scores — all from a simple API.

## Features

- **Player Management** — Add players with batting/bowling styles
- **Team Management** — Create teams, assign players
- **Match Management** — Schedule matches, record toss, start/end
- **Ball-by-Ball Scoring** — Record every delivery with runs, extras, wickets
- **Live Score** — Real-time scores via REST API + WebSocket
- **Scorecards** — Full batting & bowling scorecards per innings
- **Player Stats** — Career batting & bowling averages, strike rates, economy
- **Records** — Highest score, best bowling, most runs/wickets/sixes

## Tech Stack

- **Backend:** Python + FastAPI
- **Database:** SQLite (zero config, portable)
- **Real-time:** WebSocket for live score updates
- **Docs:** Auto-generated Swagger UI

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the server
uvicorn app.main:app --reload

# 3. Open API docs
# http://localhost:8000/docs
```

## API Endpoints

### Players
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/players/` | Create player |
| GET | `/players/` | List all players |
| GET | `/players/{id}` | Get player |
| PUT | `/players/{id}` | Update player |
| DELETE | `/players/{id}` | Delete player |

### Teams
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/teams/` | Create team |
| GET | `/teams/` | List all teams |
| GET | `/teams/{id}` | Get team with players |
| PUT | `/teams/{id}` | Update team |
| POST | `/teams/{id}/players` | Add player to team |
| DELETE | `/teams/{id}/players/{pid}` | Remove player from team |
| DELETE | `/teams/{id}` | Delete team |

### Matches
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/matches/` | Create match |
| GET | `/matches/` | List matches (filter by status) |
| GET | `/matches/{id}` | Get match details |
| POST | `/matches/{id}/toss` | Record toss |
| POST | `/matches/{id}/start` | Start match |
| POST | `/matches/{id}/end` | End match & calculate result |

### Live Scoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/scoring/innings/{id}/ball` | Record a ball |
| GET | `/scoring/match/{id}/live` | Get live score |
| GET | `/scoring/innings/{id}/scorecard` | Get full scorecard |

### Stats & Records
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stats/player/{id}` | Player career stats |
| GET | `/records/` | All-time records |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/live/{match_id}` | Real-time live score stream |

## Match Flow

```
1. Create Players   →  POST /players/
2. Create Teams     →  POST /teams/
3. Add Players      →  POST /teams/{id}/players
4. Create Match     →  POST /matches/
5. Record Toss      →  POST /matches/{id}/toss
6. Start Match      →  POST /matches/{id}/start
7. Score Ball-by-Ball → POST /scoring/innings/{id}/ball
8. Check Live Score →  GET  /scoring/match/{id}/live
9. End Match        →  POST /matches/{id}/end
10. View Records    →  GET  /records/
```

## Project Structure

```
BOXcric/
├── app/
│   ├── main.py            # FastAPI app + WebSocket
│   ├── config.py          # App configuration
│   ├── database.py        # SQLAlchemy setup
│   ├── models/            # Database models
│   │   ├── player.py      # Player model
│   │   ├── team.py        # Team + TeamPlayer models
│   │   ├── match.py       # Match model
│   │   ├── innings.py     # Innings model
│   │   └── ball.py        # Ball-by-ball model
│   ├── schemas/           # Pydantic request/response schemas
│   │   ├── player.py
│   │   ├── team.py
│   │   ├── match.py
│   │   └── score.py       # Scoring, stats, records schemas
│   ├── routers/           # API route handlers
│   │   ├── players.py
│   │   ├── teams.py
│   │   ├── matches.py
│   │   ├── scoring.py
│   │   ├── stats.py
│   │   └── records.py
│   ├── services/          # Business logic
│   │   ├── scoring.py     # Ball recording, live score, scorecard
│   │   ├── stats.py       # Player career stats
│   │   └── records.py     # All-time records
│   └── websocket/
│       └── live_score.py  # WebSocket connection manager
├── requirements.txt
├── .env.example
└── README.md
```
