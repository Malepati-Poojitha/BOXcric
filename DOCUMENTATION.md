# BOXcric — Software Requirements Specification & Design Document

## Cricket Match Management & Live Scoring Platform

| Field | Value |
|-------|-------|
| **Document ID** | BOXCRIC-SRS-SDD-001 |
| **Version** | 1.0 |
| **Date** | March 2026 |
| **Standard** | IEEE 29148-2018 (SRS), IEEE 1016-2009 (SDD), IEEE 829-2008 (Test) |
| **Status** | Approved |

### Revision History

| Version | Date | Description |
|---------|------------|----------------------------------------------|
| 0.1 | Feb 2026 | Initial draft — problem definition and scope |
| 0.5 | Feb 2026 | Added system design and database schema |
| 0.8 | Mar 2026 | Added implementation details and code |
| 0.9 | Mar 2026 | Added deployment, testing, Turso integration |
| 1.0 | Mar 2026 | Final release — IEEE restructured |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Specific Requirements](#3-specific-requirements)
4. [System Design (IEEE 1016)](#4-system-design-ieee-1016)
5. [Implementation](#5-implementation)
6. [Test Plan (IEEE 829)](#6-test-plan-ieee-829)
7. [Traceability Matrix](#7-traceability-matrix)
8. [References](#8-references)
9. [Appendices](#9-appendices)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the software requirements, system design, and test plan for **BOXcric**, a web-based cricket match management and live scoring platform. It is intended for developers, evaluators, and stakeholders involved in the development, deployment, and maintenance of the system.

This document conforms to:
- **IEEE 29148-2018** — Systems and software engineering — Life cycle processes — Requirements engineering
- **IEEE 1016-2009** — Systems design — Software design descriptions
- **IEEE 829-2008** — Standard for software and system test documentation

### 1.2 Scope

BOXcric is a full-stack web application that enables local cricket communities to:
- Create and manage teams and players
- Conduct ball-by-ball live scoring with real-time updates via WebSocket
- Track comprehensive player statistics, records, and rankings
- Provide a user-facing progressive web app for fans to follow matches, view stats, and interact
- Ensure data persistence across deployments using cloud database synchronization

The system consists of a Python FastAPI backend, Jinja2 server-rendered frontend, Turso cloud database, and WebSocket real-time layer. It is deployed on Render's free tier with zero operational cost.

**Boundaries:** The system does not include native mobile applications, payment processing, tournament/league management, or AI-based shot classification.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|-----------|
| API | Application Programming Interface |
| ASGI | Asynchronous Server Gateway Interface |
| CRUD | Create, Read, Update, Delete |
| CSS | Cascading Style Sheets |
| ER | Entity-Relationship |
| FK | Foreign Key |
| FR | Functional Requirement |
| H2H | Head-to-Head |
| HTML | HyperText Markup Language |
| HTTP | HyperText Transfer Protocol |
| JWT | JSON Web Token |
| MOM | Man of the Match |
| NFR | Non-Functional Requirement |
| ORM | Object-Relational Mapping |
| OTP | One-Time Password |
| PK | Primary Key |
| PWA | Progressive Web App |
| REST | Representational State Transfer |
| SDD | Software Design Description |
| SRS | Software Requirements Specification |
| SQL | Structured Query Language |
| SSR | Server-Side Rendering |
| TC | Test Case |
| UI | User Interface |
| UX | User Experience |
| WS | WebSocket |

### 1.4 References

| Ref | Standard / Source |
|-----|-------------------|
| [1] | IEEE 29148-2018, *Systems and software engineering — Life cycle processes — Requirements engineering* |
| [2] | IEEE 1016-2009, *Systems design — Software design descriptions* |
| [3] | IEEE 829-2008, *Standard for Software and System Test Documentation* |
| [4] | FastAPI Documentation — https://fastapi.tiangolo.com/ |
| [5] | SQLAlchemy 2.0 Documentation — https://docs.sqlalchemy.org/ |
| [6] | Turso (libsql) Documentation — https://docs.turso.tech/ |
| [7] | Pydantic Documentation — https://docs.pydantic.dev/ |
| [8] | Brevo Email API — https://developers.brevo.com/ |
| [9] | Render Deployment Docs — https://render.com/docs |
| [10] | RFC 6455: The WebSocket Protocol — https://www.rfc-editor.org/rfc/rfc6455 |
| [11] | OWASP Top 10 — https://owasp.org/www-project-top-ten/ |

### 1.5 Overview

The remainder of this document is organized as follows:
- **Section 2** provides an overall description of the product, including user characteristics, constraints, and assumptions.
- **Section 3** specifies functional and non-functional requirements with unique identifiers.
- **Section 4** presents the system design following IEEE 1016 viewpoints (architecture, data, interface, component).
- **Section 5** details the implementation with source code listings.
- **Section 6** provides the test plan and test cases per IEEE 829.
- **Section 7** presents the traceability matrix mapping requirements → design → code → tests.
- **Section 8** lists all references.

---

## 2. Overall Description

### 2.1 Product Perspective

BOXcric fills a gap in the amateur cricket technology space. Existing cricket applications (Cricbuzz, ESPNcricinfo) cater exclusively to professional tournaments, leaving local cricket communities without affordable match management infrastructure. BOXcric provides a free, self-contained platform that covers the complete match lifecycle — from player registration to post-match statistics.

The system is a standalone web application and does not depend on or interface with external cricket data providers. It operates independently on free-tier cloud services.

### 2.2 Product Functions

The system provides the following high-level functions:

| Function Group | Description |
|---------------|-------------|
| Player Management | Create, read, update, delete players with cricket profile data |
| Team Management | Create teams, assign players, designate captain/vice-captain/host |
| Match Management | Create matches, record toss, start/end matches, super overs |
| Live Scoring | Ball-by-ball recording with runs, extras, wickets, fielder info |
| Real-time Updates | WebSocket-based live score push to all connected clients |
| Statistics | Career batting & bowling stats per player |
| Records | All-time records — highest score, best bowling, team totals |
| Rankings | Weighted ranking system for batting, bowling, all-rounders |
| User System | Registration, OTP login, profile management, photo upload |
| Notifications | In-app notifications for match events to involved players |
| Win Probability | Live win percentage calculation with multiple factors |
| Commentary | Auto-generated ball-by-ball and over-by-over commentary |
| Social Features | MOM voting, predictions, emoji reactions, fantasy XI |
| Media | Video gallery and match photo uploads |
| PWA | Installable web app with offline support for static assets |
| Admin Panel | Full CRUD administration for all entities |

### 2.3 User Characteristics

| User Type | Description | Technical Skill |
|-----------|-------------|-----------------|
| Admin/Scorer | Creates matches, teams, players; performs ball-by-ball scoring | Moderate — familiar with web apps |
| Player | Registers, views own stats, records, rankings, receives notifications | Low — mobile phone user |
| Fan/Viewer | Follows live matches, views scores, reacts, predicts, picks fantasy XI | Low — mobile phone user |

### 2.4 Constraints

| ID | Constraint | Description |
|----|-----------|-------------|
| C-01 | Zero Cost | Entire platform must operate on free-tier services (Render, Turso, Brevo) |
| C-02 | Ephemeral Filesystem | Render's free tier deletes local files on redeploy — requires cloud database |
| C-03 | Single Instance | Free tier allows only one server instance — no horizontal scaling |
| C-04 | Email Limit | Brevo free tier limits to 300 emails/day for OTP delivery |
| C-05 | No Native App | PWA only — no iOS/Android app store distribution |
| C-06 | Python Runtime | Backend must run on Python 3.11.x as supported by Render |

### 2.5 Assumptions and Dependencies

| ID | Assumption/Dependency |
|----|----------------------|
| A-01 | Users have a modern web browser supporting WebSocket (RFC 6455) and Service Workers |
| A-02 | Users have internet connectivity during match scoring |
| A-03 | Turso cloud database service remains available and free-tier continues |
| A-04 | Render hosting platform remains available with Python support |
| A-05 | Brevo email API remains available for OTP delivery |
| A-06 | Cricket matches follow standard rules with minor local variations |
| A-07 | Each team has at least 2 players to start a match |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Player Management

| ID | Requirement | Priority |
|----|------------|----------|
| FR-001 | The system shall allow the admin to create a new player with name, batting style, and bowling style | High |
| FR-002 | The system shall allow the admin to view a list of all registered players | High |
| FR-003 | The system shall allow the admin to view details of a specific player by ID | High |
| FR-004 | The system shall allow the admin to update a player's name, nickname, batting style, bowling style, and phone | Medium |
| FR-005 | The system shall allow the admin to delete a player, nullifying all foreign key references in ball records | Medium |
| FR-006 | The system shall support the following batting styles: right_hand, left_hand | High |
| FR-007 | The system shall support the following bowling styles: right_arm_fast, left_arm_fast, right_arm_medium, left_arm_medium, right_arm_offspin, left_arm_orthodox, right_arm_legspin, left_arm_chinaman, none | High |

#### 3.1.2 Team Management

| ID | Requirement | Priority |
|----|------------|----------|
| FR-008 | The system shall allow the admin to create a team with a unique name | High |
| FR-009 | The system shall allow the admin to assign players to a team (many-to-many relationship) | High |
| FR-010 | The system shall allow the admin to remove a player from a team | Medium |
| FR-011 | The system shall allow the admin to designate a captain and vice-captain from team players | Medium |
| FR-012 | The system shall allow the admin to assign a host and co-host (users with scoring permissions) to a team | Medium |
| FR-013 | The system shall allow the admin to delete a team | Medium |

#### 3.1.3 Match Management

| ID | Requirement | Priority |
|----|------------|----------|
| FR-014 | The system shall allow the admin to create a match specifying two teams, number of overs, venue, and date | High |
| FR-015 | The system shall track match status through the lifecycle: SCHEDULED → TOSS → LIVE → COMPLETED | High |
| FR-016 | The system shall allow the admin to record toss result (winner and decision: bat/bowl) | High |
| FR-017 | Upon toss recording, the system shall automatically create two innings records based on toss decision | High |
| FR-018 | The system shall allow the admin to start a match (transition status to LIVE) | High |
| FR-019 | The system shall allow the admin to end a match, automatically calculating the result and winner | High |
| FR-020 | The system shall compute result summary text (e.g., "Team A won by 5 runs", "Team B won by 3 wickets") | High |
| FR-021 | The system shall support super overs for tied matches (1 over, max 2 wickets per side) | Medium |
| FR-022 | The system shall support the ABANDONED match status | Low |
| FR-023 | The system shall support the INNINGS_BREAK status between innings | Medium |

#### 3.1.4 Live Scoring

| ID | Requirement | Priority |
|----|------------|----------|
| FR-024 | The system shall record each ball delivery with: batter, bowler, non-striker, runs scored, extra type, extra runs, wicket info, and fielder | High |
| FR-025 | The system shall classify deliveries as legal or illegal (wides and no-balls are illegal) | High |
| FR-026 | The system shall not count illegal deliveries (wides, no-balls) as balls faced | High |
| FR-027 | The system shall auto-increment the over count after 6 legal deliveries | High |
| FR-028 | The system shall update innings totals (runs, wickets, overs, extras) after every ball | High |
| FR-029 | The system shall auto-complete an innings when: all batters are out, allocated overs are bowled, or target is chased | High |
| FR-030 | The system shall support the following extra types: wide, no_ball, bye, leg_bye, none | High |
| FR-031 | The system shall support the following wicket types: bowled, caught, lbw, run_out, stumped, hit_wicket, retired | High |
| FR-032 | The system shall allow undoing the last ball scored, reversing its effect on innings totals | High |
| FR-033 | The system shall limit undo to one correction per ball position (is_correction flag) | High |
| FR-034 | The system shall track the dismissed player and fielder involved for each wicket | Medium |

#### 3.1.5 Real-time Updates

| ID | Requirement | Priority |
|----|------------|----------|
| FR-035 | The system shall provide a WebSocket endpoint at /ws/live/{match_id} for live score updates | High |
| FR-036 | The system shall broadcast updated score data to all WebSocket clients connected to a match after every ball | High |
| FR-037 | The system shall provide a REST endpoint GET /scoring/match/{id}/live for polling-based live score | High |
| FR-038 | The system shall provide full scorecard data via GET /scoring/innings/{id}/scorecard | High |

#### 3.1.6 Statistics and Records

| ID | Requirement | Priority |
|----|------------|----------|
| FR-039 | The system shall compute career batting statistics per player: matches, innings, runs, average, strike rate, highest score, 50s, 100s, 4s, 6s, not-outs | High |
| FR-040 | The system shall compute career bowling statistics per player: overs, wickets, runs conceded, average, economy, best figures, 3-wicket hauls, 5-wicket hauls | High |
| FR-041 | The system shall maintain all-time records: highest individual score, best bowling, most runs, most wickets, most sixes, highest team total, lowest team total | High |
| FR-042 | The system shall compute weighted rankings for batting, bowling, and all-rounders | Medium |
| FR-043 | The system shall support head-to-head (H2H) statistics between two players | Low |

#### 3.1.7 User System and Authentication

| ID | Requirement | Priority |
|----|------------|----------|
| FR-044 | The system shall allow user registration with name, email, and password | High |
| FR-045 | The system shall hash user passwords using bcrypt before storage | High |
| FR-046 | The system shall support OTP-based login via email | High |
| FR-047 | The system shall generate 6-digit OTP codes with 5-minute expiry | High |
| FR-048 | The system shall send OTP emails via Brevo HTTP API | High |
| FR-049 | The system shall issue JWT tokens with 365-day expiry upon successful authentication | High |
| FR-050 | The system shall store JWT tokens as httponly cookies (boxcric_token) | High |
| FR-051 | The system shall auto-create user accounts for new email addresses during OTP login | Medium |
| FR-052 | The system shall allow users to update their profile (name, nickname, age, batting hand, bowling type, player role) | Medium |
| FR-053 | The system shall limit profile edits on key fields (batting hand, bowling type, role) to 5 times | Medium |
| FR-054 | The system shall synchronize user profile data to the corresponding Player record | Medium |
| FR-055 | The system shall support admin role designation via is_admin flag | Medium |

#### 3.1.8 Notifications

| ID | Requirement | Priority |
|----|------------|----------|
| FR-056 | The system shall create in-app notifications for all users involved in a match when: match is created, toss is recorded, match starts, match ends | High |
| FR-057 | The system shall identify involved users as: all players in both teams (via Player.user_id) plus team hosts and co-hosts | High |
| FR-058 | The system shall display unread notification count as a badge on the bell icon | Medium |
| FR-059 | The system shall allow users to mark individual notifications or all notifications as read | Medium |
| FR-060 | The system shall auto-poll notifications every 30 seconds via client-side JavaScript | Medium |

#### 3.1.9 Advanced Features

| ID | Requirement | Priority |
|----|------------|----------|
| FR-061 | The system shall generate ball-by-ball text commentary automatically based on scoring data | Low |
| FR-062 | The system shall generate over-summary commentary | Low |
| FR-063 | The system shall calculate live win probability based on run rate, wickets, overs remaining, and target pressure | Low |
| FR-064 | The system shall support MOM (Man of the Match) voting — one vote per user per match | Low |
| FR-065 | The system shall support match winner predictions by users | Low |
| FR-066 | The system shall support emoji reactions to match events (🔥🎉😱👏) | Low |
| FR-067 | The system shall support fantasy XI selection by users | Low |
| FR-068 | The system shall auto-detect milestones: 50, 100 (batting); 3-wicket haul, 5-wicket haul (bowling) | Low |

#### 3.1.10 Media

| ID | Requirement | Priority |
|----|------------|----------|
| FR-069 | The system shall allow uploading match videos or adding YouTube links | Low |
| FR-070 | The system shall allow uploading match photos | Low |

#### 3.1.11 Frontend

| ID | Requirement | Priority |
|----|------------|----------|
| FR-071 | The system shall provide an admin panel at /admin for full CRUD operations | High |
| FR-072 | The system shall provide a user-facing app at /app for read-only access and social features | High |
| FR-073 | The system shall support dark and light themes, persisted in localStorage | Medium |
| FR-074 | The system shall be installable as a PWA on mobile devices | Medium |
| FR-075 | The system shall cache only static assets via Service Worker (never HTML or API responses) | High |

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Metric |
|----|------------|--------|
| NFR-001 | WebSocket score updates shall be delivered to connected clients within 1 second of ball recording | Latency < 1s |
| NFR-002 | REST API endpoints shall respond within 2 seconds under normal load | Response time < 2s |
| NFR-003 | Page load time shall be under 3 seconds on 4G mobile network | Load time < 3s |

#### 3.2.2 Reliability

| ID | Requirement | Metric |
|----|------------|--------|
| NFR-004 | The system shall persist all data in Turso cloud database, surviving server restarts and redeployments | Zero data loss |
| NFR-005 | The system shall synchronize local replica with Turso cloud on every database commit | Sync on every commit |
| NFR-006 | The system shall auto-recover data on startup by pulling from Turso cloud via sync() | Full recovery on restart |

#### 3.2.3 Security

| ID | Requirement | Category |
|----|------------|----------|
| NFR-007 | User passwords shall be hashed using bcrypt with random salt — never stored in plain text | Authentication |
| NFR-008 | JWT tokens shall be stored as httponly cookies to prevent JavaScript access | Session management |
| NFR-009 | Cookies shall use SameSite=Lax to mitigate CSRF attacks | CSRF protection |
| NFR-010 | OTP codes shall expire after 5 minutes and be consumed on successful verification (one-time use) | Authentication |
| NFR-011 | Admin panel shall require is_admin=True flag on User record | Authorization |
| NFR-012 | Service Worker shall never cache HTML pages or API responses to prevent cross-user session leakage | Data isolation |

#### 3.2.4 Usability

| ID | Requirement | Description |
|----|------------|-------------|
| NFR-013 | The UI shall be responsive for screen widths ≥ 320px | Mobile-first design |
| NFR-014 | The UI shall provide a bottom navigation bar on mobile (≤ 768px) and horizontal top nav on desktop | Responsive layout |
| NFR-015 | The system shall display toast notifications for success/error feedback on user actions | User feedback |
| NFR-016 | The system shall provide confirmation dialogs for destructive actions (delete player, undo ball) | Safety |

#### 3.2.5 Scalability

| ID | Requirement | Description |
|----|------------|-------------|
| NFR-017 | The system shall support at least 50 concurrent WebSocket connections per match | Concurrent users |
| NFR-018 | The system shall handle at least 100 registered players and 50 matches | Data volume |

#### 3.2.6 Portability

| ID | Requirement | Description |
|----|------------|-------------|
| NFR-019 | The system shall support SQLite, PostgreSQL, and Turso (libsql) as database backends via configuration | Database portability |
| NFR-020 | The system shall auto-detect database type from DATABASE_URL environment variable | Configuration |

#### 3.2.7 Maintainability

| ID | Requirement | Description |
|----|------------|-------------|
| NFR-021 | The system shall separate concerns into layers: models, routers, schemas, services, websocket | Modular architecture |
| NFR-022 | The system shall use Pydantic schemas for request/response validation | Input validation |
| NFR-023 | The system shall auto-generate API documentation via FastAPI's Swagger UI at /docs | Self-documenting |

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

| Interface | Description |
|-----------|-------------|
| Admin Panel (/admin) | Server-rendered HTML pages for full CRUD operations, ball-by-ball scoring console with circular run buttons (0–6), wicket panel, undo button |
| User App (/app) | Server-rendered HTML pages for match viewing, stats, rankings; notification bell with dropdown; login popup for unauthenticated users |
| Swagger UI (/docs) | Auto-generated interactive API documentation |

#### 3.3.2 Hardware Interfaces

None. The system operates entirely as a web application.

#### 3.3.3 Software Interfaces

| Interface | Protocol | Description |
|-----------|----------|-------------|
| Turso Cloud Database | libsql (SQLite wire protocol) | Data persistence via embedded replica sync |
| Brevo Email API | HTTPS REST | OTP email delivery (POST to api.brevo.com/v3/smtp/email) |
| Browser WebSocket | WSS (RFC 6455) | Real-time live score push to clients |

#### 3.3.4 Communication Interfaces

| Protocol | Endpoint Pattern | Purpose |
|----------|-----------------|---------|
| HTTP/HTTPS | /players/, /teams/, /matches/, etc. | RESTful API for CRUD operations |
| HTTP/HTTPS | /admin/*, /app/* | Server-rendered HTML pages |
| WebSocket | /ws/live/{match_id} | Real-time score broadcasting |
| HTTPS | api.brevo.com/v3/smtp/email | Outbound OTP email delivery |

---

## 4. System Design (IEEE 1016)

### 4.1 Design Viewpoints

This section follows IEEE 1016-2009 and presents the system design through four viewpoints:

| Viewpoint | Description | Corresponds To |
|-----------|-------------|---------------|
| Architecture Viewpoint | High-level component structure and interactions | §4.2 |
| Data Viewpoint | Database schema, entity relationships | §4.3 |
| Interface Viewpoint | API endpoints, WebSocket protocol, external APIs | §4.4 |
| Component Viewpoint | Internal module design, service layer, algorithms | §4.5 |

### 4.2 Architecture Viewpoint

#### 4.2.1 System Architecture Diagram

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

#### 4.2.2 Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Language | Python | 3.11.11 | Mature ecosystem, async support |
| Web Framework | FastAPI | 0.135+ | Async, auto-docs, WebSocket built-in |
| ORM | SQLAlchemy | 2.0+ | Mature, multi-database support |
| Database (production) | Turso (libsql-experimental) | 0.0.55 | Free tier, cloud-persistent, edge replicas |
| Database (local) | SQLite | Built-in | Zero-config development fallback |
| Auth | python-jose (JWT) + bcrypt | — | Stateless tokens, secure hashing |
| Template Engine | Jinja2 | 3.1+ | No build step, server-rendered |
| ASGI Server | Uvicorn | — | High-performance async server |
| Email | Brevo HTTP API | — | Free 300 emails/day |
| Hosting | Render (free tier) | — | Auto-deploy from GitHub |

#### 4.2.3 Project Structure

```
BOXcric/
├── app/
│   ├── main.py              # FastAPI app, routes, startup, migrations
│   ├── config.py            # Environment config (DATABASE_URL, etc.)
│   ├── database.py          # SQLAlchemy engine + Turso libsql connection
│   ├── auth.py              # JWT, password hashing, OTP, cookie auth
│   ├── models/              # SQLAlchemy table models (14 tables)
│   │   ├── user.py, player.py, team.py
│   │   ├── match.py, innings.py, ball.py
│   │   └── notification.py, extras.py, video.py
│   ├── routers/             # API endpoint handlers (13 routers)
│   │   ├── matches.py, scoring.py, players.py
│   │   ├── teams.py, stats.py, records.py
│   │   └── user_auth.py, notifications.py, ...
│   ├── schemas/             # Pydantic request/response models
│   ├── services/            # Business logic (scoring, stats, rankings, etc.)
│   └── websocket/           # WebSocket connection manager
├── templates/               # Jinja2 HTML templates (admin + user)
├── static/                  # CSS, JS, icons, uploads, PWA files
├── requirements.txt         # Python dependencies
├── Procfile                 # Render start command
└── runtime.txt              # Python version pin (3.11.11)
```

#### 4.2.4 Layer Architecture

| Layer | Responsibility | Files |
|-------|---------------|-------|
| Models | SQLAlchemy declarative models defining all 14 database tables with relationships and enums | app/models/*.py |
| Routers | FastAPI route handlers for each resource group; input validation via Pydantic | app/routers/*.py |
| Schemas | Pydantic models for request/response validation and serialization | app/schemas/*.py |
| Services | Business logic separated from HTTP concerns; reusable across routes | app/services/*.py |
| WebSocket | Connection manager tracking clients per match; broadcasts on every ball | app/websocket/*.py |
| Templates | Jinja2 HTML templates with template inheritance (base → child) | templates/*.html |
| Static | CSS, JavaScript, icons, PWA manifest, Service Worker | static/* |

### 4.3 Data Viewpoint

#### 4.3.1 Entity-Relationship Diagram

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

#### 4.3.2 Table Definitions

**Users Table**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, auto-increment | Unique user identifier |
| name | String(100) | NOT NULL | Display name |
| nickname | String(50) | nullable | Optional nickname |
| email | String(200) | NOT NULL, UNIQUE, INDEX | Login identifier |
| phone | String(15) | nullable | Contact number |
| hashed_password | String(200) | NOT NULL | bcrypt hash |
| is_active | Boolean | default=True | Account status |
| created_at | DateTime | default=utcnow | Registration timestamp |
| photo | String(300) | nullable | Profile photo URL |
| age | Integer | nullable | Player age |
| batting_hand | String(20) | nullable | right / left |
| bowling_hand | String(20) | nullable | right / left / none |
| bowling_type | String(30) | nullable | fast / medium / offspin / etc. |
| gender | String(10) | nullable | Male / Female |
| player_role | String(30) | nullable | batsman / bowler / allrounder / wk_batsman |
| profile_complete | Boolean | default=False | Profile setup status |
| profile_edits | Integer | default=0 | Edit count (max 5) |
| is_admin | Boolean | default=False | Admin access flag |

**Players Table**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, auto-increment | Unique player identifier |
| name | String(100) | NOT NULL | Player name |
| nickname | String(50) | nullable | Display nickname |
| batting_style | Enum(BattingStyle) | default=RIGHT_HAND | right_hand / left_hand |
| bowling_style | Enum(BowlingStyle) | default=NONE | 8 bowling styles + none |
| phone | String(15) | nullable | Contact number |
| player_role | String(30) | nullable | Playing role |
| user_id | Integer | FK → users.id, nullable | Linked user account |

**Teams Table**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, auto-increment | Unique team identifier |
| name | String(100) | NOT NULL, UNIQUE | Team name |
| short_name | String(10) | nullable | Abbreviation |
| captain_id | Integer | FK → players.id, nullable | Team captain |
| vice_captain_id | Integer | FK → players.id, nullable | Vice captain |
| host_id | Integer | FK → users.id, nullable | Scorer permission |
| cohost_id | Integer | FK → users.id, nullable | Scorer permission |

**TeamPlayers Table** (Junction)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK | Entry identifier |
| team_id | Integer | FK → teams.id, NOT NULL | Team reference |
| player_id | Integer | FK → players.id, NOT NULL | Player reference |

**Matches Table**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, auto-increment | Unique match identifier |
| title | String(200) | nullable | Match title |
| team1_id | Integer | FK → teams.id, NOT NULL | First team |
| team2_id | Integer | FK → teams.id, NOT NULL | Second team |
| overs | Integer | NOT NULL, default=20 | Overs per innings |
| venue | String(200) | nullable | Match venue |
| date | DateTime | default=utcnow | Match date |
| status | Enum(MatchStatus) | default=SCHEDULED | Lifecycle state |
| toss_winner_id | Integer | FK → teams.id, nullable | Toss winner |
| toss_decision | Enum(TossDecision) | nullable | bat / bowl |
| winner_id | Integer | FK → teams.id, nullable | Match winner |
| result_summary | String(300) | nullable | Result text |

**Innings Table**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, auto-increment | Unique innings identifier |
| match_id | Integer | FK → matches.id, NOT NULL | Parent match |
| innings_number | Integer | NOT NULL | 1, 2, or 3+ (super over) |
| batting_team_id | Integer | FK → teams.id, NOT NULL | Batting team |
| bowling_team_id | Integer | FK → teams.id, NOT NULL | Bowling team |
| total_runs | Integer | default=0 | Running total |
| total_wickets | Integer | default=0 | Wickets fallen |
| total_overs | Integer | default=0 | Completed overs |
| total_balls | Integer | default=0 | Balls in current over (0–5) |
| extras | Integer | default=0 | Total extras |
| is_completed | Boolean | default=False | Innings finished |

**Balls Table**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, auto-increment | Unique ball identifier |
| innings_id | Integer | FK → innings.id, NOT NULL | Parent innings |
| over_number | Integer | NOT NULL | Over (0-indexed) |
| ball_number | Integer | NOT NULL | Ball within over (1–6) |
| batter_id | Integer | FK → players.id, NOT NULL | Batter on strike |
| bowler_id | Integer | FK → players.id, NOT NULL | Bowler |
| non_striker_id | Integer | FK → players.id, nullable | Non-striker |
| runs_scored | Integer | default=0 | Runs off the bat |
| extra_type | Enum(ExtraType) | default=NONE | wide / no_ball / bye / leg_bye / none |
| extra_runs | Integer | default=0 | Extra runs |
| is_wicket | Boolean | default=False | Wicket fell |
| wicket_type | Enum(WicketType) | default=NONE | bowled / caught / lbw / etc. |
| dismissed_player_id | Integer | FK → players.id, nullable | Batter dismissed |
| fielder_id | Integer | FK → players.id, nullable | Fielder involved |
| is_legal | Boolean | default=True | False for wides/no-balls |
| is_correction | Boolean | default=False | Re-scored after undo |

**Notifications Table**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, auto-increment | Notification identifier |
| user_id | Integer | FK → users.id, NOT NULL, INDEX | Recipient |
| match_id | Integer | FK → matches.id, nullable | Related match |
| type | String(50) | NOT NULL | Event type |
| title | String(200) | NOT NULL | Notification title |
| message | String(500) | NOT NULL | Notification body |
| is_read | Boolean | default=False | Read status |
| created_at | DateTime | default=utcnow | Timestamp |

**Additional Models** (in extras.py):
- **MatchPhoto** — photos per match
- **MOMVote** — Man of the Match votes (one per user per match)
- **MatchPrediction** — user predictions for match winner
- **Reaction** — emoji reactions (🔥🎉😱👏)
- **Milestone** — auto-awarded badges (century, 50, 5W, 3W)

### 4.4 Interface Viewpoint

#### 4.4.1 REST API Endpoints

**Players API**

| Method | Endpoint | Description | Auth | Maps To |
|--------|----------|-------------|------|---------|
| POST | /players/ | Create player | Admin | FR-001 |
| GET | /players/ | List all players | None | FR-002 |
| GET | /players/{id} | Get player details | None | FR-003 |
| PUT | /players/{id} | Update player | Admin | FR-004 |
| DELETE | /players/{id} | Delete player | Admin | FR-005 |

**Teams API**

| Method | Endpoint | Description | Auth | Maps To |
|--------|----------|-------------|------|---------|
| POST | /teams/ | Create team | Admin | FR-008 |
| GET | /teams/ | List all teams | None | FR-008 |
| GET | /teams/{id} | Get team with players | None | FR-008 |
| PUT | /teams/{id} | Update team | Admin | FR-008 |
| POST | /teams/{id}/players | Add player to team | Admin | FR-009 |
| DELETE | /teams/{id}/players/{pid} | Remove player | Admin | FR-010 |
| DELETE | /teams/{id} | Delete team | Admin | FR-013 |

**Matches API**

| Method | Endpoint | Description | Auth | Maps To |
|--------|----------|-------------|------|---------|
| POST | /matches/ | Create match | Admin | FR-014 |
| GET | /matches/ | List matches (filter by status) | None | FR-015 |
| GET | /matches/{id} | Get match details | None | FR-015 |
| POST | /matches/{id}/toss | Record toss | Admin | FR-016 |
| POST | /matches/{id}/start | Start match | Admin | FR-018 |
| POST | /matches/{id}/end | End match | Admin | FR-019 |
| POST | /matches/{id}/super-over | Start super over | Admin | FR-021 |

**Scoring API**

| Method | Endpoint | Description | Auth | Maps To |
|--------|----------|-------------|------|---------|
| POST | /scoring/innings/{id}/ball | Record a ball | Admin | FR-024 |
| GET | /scoring/match/{id}/live | Get live score | None | FR-037 |
| GET | /scoring/innings/{id}/scorecard | Get full scorecard | None | FR-038 |
| DELETE | /undo/{innings_id} | Undo last ball | Admin | FR-032 |

**Stats & Records API**

| Method | Endpoint | Description | Auth | Maps To |
|--------|----------|-------------|------|---------|
| GET | /stats/player/{id} | Player career stats | None | FR-039, FR-040 |
| GET | /records/ | All-time records | None | FR-041 |
| GET | /rankings/ | Player rankings | None | FR-042 |
| GET | /stats/h2h/{p1}/{p2} | Head-to-head | None | FR-043 |

**User Auth API**

| Method | Endpoint | Description | Auth | Maps To |
|--------|----------|-------------|------|---------|
| POST | /api/user/register | Register | None | FR-044 |
| POST | /api/user/forgot-password | Send OTP | None | FR-046 |
| POST | /api/user/verify-otp | Verify OTP & login | None | FR-046 |
| POST | /api/user/profile | Update profile | User | FR-052 |

**Notifications API**

| Method | Endpoint | Description | Auth | Maps To |
|--------|----------|-------------|------|---------|
| GET | /api/notifications/ | Get user notifications | User | FR-058 |
| POST | /api/notifications/{id}/read | Mark one as read | User | FR-059 |
| POST | /api/notifications/read-all | Mark all as read | User | FR-059 |

#### 4.4.2 WebSocket Interface

| Endpoint | Direction | Data Format | Maps To |
|----------|-----------|-------------|---------|
| /ws/live/{match_id} | Server → Client | JSON (score summary) | FR-035, FR-036 |

#### 4.4.3 External API Interface — Brevo

| Field | Value |
|-------|-------|
| URL | https://api.brevo.com/v3/smtp/email |
| Method | POST |
| Auth | api-key header |
| Purpose | Send OTP emails |
| Maps To | FR-048 |

### 4.5 Component Viewpoint

#### 4.5.1 Data Flow — Live Scoring

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

#### 4.5.2 Data Flow — Authentication

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

#### 4.5.3 Data Flow — Database Persistence (Turso)

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

#### 4.5.4 Component — Match State Machine

```
    SCHEDULED ──── record toss ────► TOSS
                                      │
                                 start match
                                      │
                                      ▼
    ABANDONED ◄─────────────────── LIVE ──── innings ends ──► INNINGS_BREAK
                                      │                            │
                                 end match                    resume
                                      │                            │
                                      ▼                            ▼
                                 COMPLETED ◄──────────────────── LIVE
                                      │
                                 (if tied)
                                      │
                                      ▼
                                 super over → LIVE (again)
```

#### 4.5.5 Component — WebSocket Connection Manager

```python
class ConnectionManager:
    active_connections: dict[int, list[WebSocket]] = {}

    async def connect(websocket, match_id):
        # Accept connection, add to match_id list

    def disconnect(websocket, match_id):
        # Remove from match_id list

    async def broadcast(match_id, data):
        # Send JSON to all clients watching this match
```

---

## 5. Implementation

### 5.1 Configuration Module

**`app/config.py`** — Loads environment variables and determines database URL.

```python
import os
from dotenv import load_dotenv
load_dotenv()

_db_url = os.getenv("DATABASE_URL", "")
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
if not _db_url or not _db_url.startswith(("sqlite", "postgresql", "mysql", "libsql")):
    DATABASE_URL = "sqlite:///./boxcric.db"
else:
    DATABASE_URL = _db_url
APP_TITLE = "BOXcric"
APP_VERSION = "1.0.0"
```

**Implements:** NFR-019, NFR-020

### 5.2 Database Module — Turso Integration

**`app/database.py`** — Creates SQLAlchemy engine with Turso cloud sync.

```python
if _is_libsql:
    import libsql_experimental as libsql

    class _LibsqlConnectionWrapper:
        def __init__(self):
            self._conn = libsql.connect(
                "turso_replica.db", sync_url=_turso_url, auth_token=_auth_token
            )
            self._conn.sync()  # Pull latest data from Turso cloud on startup

        def commit(self):
            self._conn.commit()
            self._conn.sync()  # Push changes to Turso cloud after every commit

    _shared_conn = _LibsqlConnectionWrapper()
    engine = create_engine("sqlite://", creator=lambda: _shared_conn, poolclass=StaticPool)
```

**Implements:** NFR-004, NFR-005, NFR-006

### 5.3 Authentication Module

**`app/auth.py`** — Handles JWT tokens, password hashing, OTP generation, and email sending.

```python
SECRET_KEY = os.getenv("SECRET_KEY", "boxcric-secret-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8760  # 365 days

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def generate_otp(identifier: str, user_id: int) -> str:
    otp = str(random.randint(100000, 999999))
    _otp_store[identifier] = {
        "otp": otp,
        "expires": datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES),
        "user_id": user_id,
    }
    return otp

def get_current_user_from_cookie(request: Request, db):
    token = request.cookies.get("boxcric_token")
    if not token: return None
    payload = decode_token(token)
    if not payload: return None
    user_id = int(payload.get("sub", 0))
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()
```

**Implements:** FR-045, FR-046, FR-047, FR-049, FR-050, NFR-007, NFR-008, NFR-010

### 5.4 Scoring Engine

**`app/services/scoring.py`** — The core ball-by-ball scoring logic.

```python
def record_ball(db: Session, innings_id: int, data: BallInput) -> Ball:
    innings = db.query(Innings).filter(Innings.id == innings_id).first()
    if not innings: raise ValueError("Innings not found")
    if innings.is_completed: raise ValueError("Innings is already completed")

    is_legal = data.extra_type not in (ExtraType.WIDE, ExtraType.NO_BALL)

    if is_legal:
        current_ball = innings.total_balls + 1
        over_number = innings.total_overs
        if current_ball >= 6:
            innings.total_overs += 1
            innings.total_balls = 0
        else:
            innings.total_balls = current_ball
    else:
        over_number = innings.total_overs

    ball = Ball(innings_id=innings_id, over_number=over_number, ...)
    db.add(ball)

    innings.total_runs += data.runs_scored + data.extra_runs
    innings.extras += data.extra_runs
    if data.is_wicket: innings.total_wickets += 1

    # Auto-complete check
    if innings.total_wickets >= max_wickets or innings.total_overs >= overs_limit:
        innings.is_completed = True

    # Target chased check (2nd innings)
    if innings.innings_number % 2 == 0:
        if innings.total_runs > prev_innings.total_runs:
            innings.is_completed = True

    db.commit()
    return ball
```

**Implements:** FR-024 through FR-034

### 5.5 Notification Service

**`app/services/notifications.py`**

```python
def get_match_user_ids(db, match) -> set[int]:
    # Get user_ids of all players in both teams + hosts/cohosts
    ...

def notify_match_users(db, match, notif_type, title, message):
    for uid in get_match_user_ids(db, match):
        db.add(Notification(user_id=uid, match_id=match.id,
            type=notif_type, title=title, message=message))
    db.commit()
```

**Implements:** FR-056, FR-057

### 5.6 WebSocket Manager

**`app/websocket/live_score.py`**

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket, match_id):
        await websocket.accept()
        self.active_connections.setdefault(match_id, []).append(websocket)

    async def broadcast(self, match_id, data):
        for ws in self.active_connections.get(match_id, []):
            try: await ws.send_json(data)
            except: pass

manager = ConnectionManager()
```

**Implements:** FR-035, FR-036, NFR-001

### 5.7 Undo/Correction System

**`app/routers/features.py`**

```python
@router.delete("/undo/{innings_id}")
def undo_last_ball(innings_id, db):
    last_ball = db.query(Ball).filter(Ball.innings_id == innings_id)\
        .order_by(Ball.id.desc()).first()
    if last_ball.is_correction:
        raise HTTPException(400, "Already corrected once.")

    inn.total_runs -= (last_ball.runs_scored + last_ball.extra_runs)
    inn.extras -= last_ball.extra_runs
    if last_ball.is_wicket: inn.total_wickets -= 1
    if last_ball.is_legal:
        if inn.total_balls > 0: inn.total_balls -= 1
        else: inn.total_overs -= 1; inn.total_balls = 5
    inn.is_completed = False
    db.delete(last_ball)
    db.commit()
    return {"detail": "Ball undone.", "is_correction": True}
```

**Implements:** FR-032, FR-033

### 5.8 Service Worker (PWA)

**`static/sw.js`**

```javascript
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  const isStaticAsset = url.pathname.startsWith('/static/');
  const isApiOrPage = url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/app') || url.pathname.startsWith('/admin');

  if (isApiOrPage && !isStaticAsset) {
    event.respondWith(fetch(event.request)); // Never cache pages/API
    return;
  }
  // Static: network-first with cache fallback
  event.respondWith(
    fetch(event.request).then(response => {
      if (response.ok) {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
      }
      return response;
    }).catch(() => caches.match(event.request))
  );
});
```

**Implements:** FR-074, FR-075, NFR-012

### 5.9 Frontend JavaScript

**`static/js/app.js`** — Theme toggle, API helper, toast notifications, match card builder, PWA registration, pull-to-refresh, haptic feedback.

**Implements:** FR-071, FR-072, FR-073, NFR-013, NFR-014, NFR-015, NFR-016

### 5.10 CSS Stylesheet

**`static/css/style.css`** (1,972 lines) — Complete UI styling with CSS custom properties for theming:

```css
:root {
  --primary: #1a472a;
  --accent: #e63946;
  --bg: #f0f2f5;
  --card-bg: #ffffff;
  --text: #1a1a2e;
}

[data-theme="dark"] {
  --bg: #0f1419;
  --card-bg: #1a2332;
  --text: #e7e9ea;
}
```

**Implements:** FR-073, NFR-013, NFR-014

---

## 6. Test Plan (IEEE 829)

### 6.1 Test Plan Identifier

**TP-BOXCRIC-001** — BOXcric System Test Plan v1.0

### 6.2 Test Items

| Item | Version | Description |
|------|---------|-------------|
| BOXcric Backend | 1.0 | FastAPI application (app/) |
| BOXcric Frontend | 1.0 | Templates + static assets |
| Turso Integration | 1.0 | Database persistence layer |
| WebSocket Layer | 1.0 | Live score broadcasting |

### 6.3 Features to be Tested

All functional requirements FR-001 through FR-075 and non-functional requirements NFR-001 through NFR-023 as specified in Section 3.

### 6.4 Features Not to be Tested

- Browser rendering across all versions (tested on Chrome, Safari, Firefox latest)
- Turso cloud infrastructure reliability (external dependency)
- Brevo email delivery reliability (external dependency)

### 6.5 Test Environment

| Component | Specification |
|-----------|--------------|
| OS | macOS / Linux |
| Python | 3.11.11 |
| Database | Turso cloud (production) / SQLite (local) |
| Server | Uvicorn (local) / Render (production) |
| Browser | Chrome 120+, Safari 17+, Firefox 120+ |

### 6.6 Pass/Fail Criteria

- A test case **passes** if the actual result matches the expected result.
- A test case **fails** if the actual result differs from the expected result, or an unhandled error occurs.
- The system passes acceptance testing if all High-priority test cases pass and at least 80% of Medium/Low-priority test cases pass.

### 6.7 Test Cases

#### 6.7.1 Player Management Tests

| TC-ID | Description | Precondition | Input | Expected Result | Priority | Maps To |
|-------|-------------|-------------|-------|-----------------|----------|---------|
| TC-001 | Create a player | Server running | POST /players/ with name="Test Player", batting_style="right_hand" | 200 OK, player object returned with id | High | FR-001 |
| TC-002 | List all players | At least 1 player exists | GET /players/ | 200 OK, array of player objects | High | FR-002 |
| TC-003 | Get player by ID | Player id=1 exists | GET /players/1 | 200 OK, player object with id=1 | High | FR-003 |
| TC-004 | Update player | Player id=1 exists | PUT /players/1 with name="Updated" | 200 OK, updated player object | Medium | FR-004 |
| TC-005 | Delete player | Player id=1 exists, referenced in balls | DELETE /players/1 | 200 OK, ball FK refs set to NULL, player deleted | Medium | FR-005 |
| TC-006 | Get non-existent player | No player id=999 | GET /players/999 | 404 Not Found | High | FR-003 |

#### 6.7.2 Team Management Tests

| TC-ID | Description | Precondition | Input | Expected Result | Priority | Maps To |
|-------|-------------|-------------|-------|-----------------|----------|---------|
| TC-007 | Create team | Server running | POST /teams/ with name="Team Alpha" | 200 OK, team object with id | High | FR-008 |
| TC-008 | Add player to team | Team id=1 and player id=1 exist | POST /teams/1/players with player_id=1 | 200 OK, player added | High | FR-009 |
| TC-009 | Remove player from team | Player 1 is in team 1 | DELETE /teams/1/players/1 | 200 OK, player removed | Medium | FR-010 |
| TC-010 | Create duplicate team name | Team "Alpha" exists | POST /teams/ with name="Alpha" | 400 Bad Request | Medium | FR-008 |

#### 6.7.3 Match Lifecycle Tests

| TC-ID | Description | Precondition | Input | Expected Result | Priority | Maps To |
|-------|-------------|-------------|-------|-----------------|----------|---------|
| TC-011 | Create match | Two teams exist with players | POST /matches/ with team1_id, team2_id, overs=10 | 200 OK, match with status=SCHEDULED | High | FR-014 |
| TC-012 | Record toss | Match id=1 in SCHEDULED status | POST /matches/1/toss with winner, decision=bat | 200 OK, status=TOSS, 2 innings created | High | FR-016, FR-017 |
| TC-013 | Start match | Match id=1 in TOSS status | POST /matches/1/start | 200 OK, status=LIVE | High | FR-018 |
| TC-014 | End match | Match id=1 in LIVE, both innings completed | POST /matches/1/end | 200 OK, status=COMPLETED, winner set, result_summary populated | High | FR-019, FR-020 |
| TC-015 | Notifications sent on match creation | Users linked to players in both teams | Create match | Notification records created for all involved users | High | FR-056 |
| TC-016 | Start super over | Match tied | POST /matches/1/super-over | 200 OK, 2 new innings (innings_number > 2), status=LIVE | Medium | FR-021 |

#### 6.7.4 Scoring Engine Tests

| TC-ID | Description | Precondition | Input | Expected Result | Priority | Maps To |
|-------|-------------|-------------|-------|-----------------|----------|---------|
| TC-017 | Record legal ball (2 runs) | Innings id=1 active | POST ball: runs=2, extra=none | Ball created, innings.total_runs += 2, total_balls += 1 | High | FR-024, FR-028 |
| TC-018 | Record wide | Innings active | POST ball: extra_type=wide, extra_runs=1 | Ball created with is_legal=False, total_runs += 1, total_balls unchanged | High | FR-025, FR-026 |
| TC-019 | Record no-ball | Innings active | POST ball: extra_type=no_ball, extra_runs=1 | Ball with is_legal=False, extras += 1 | High | FR-025 |
| TC-020 | Over auto-increment | 5 legal balls bowled in current over | POST 6th legal ball | total_overs += 1, total_balls reset to 0 | High | FR-027 |
| TC-021 | Wicket recording | Innings active | POST ball: is_wicket=true, wicket_type=caught, dismissed_player_id, fielder_id | Ball with wicket data, total_wickets += 1 | High | FR-024, FR-034 |
| TC-022 | All out auto-completion | Team has N players, N-1 wickets fallen | Record Nth wicket | innings.is_completed = True | High | FR-029 |
| TC-023 | Overs done auto-completion | 10-over match, 9.5 overs bowled | Record 6th ball of 10th over | innings.is_completed = True | High | FR-029 |
| TC-024 | Target chased auto-completion | 2nd innings, target = 100 | Total runs reach 101 | innings.is_completed = True | High | FR-029 |
| TC-025 | Record boundary (4) | Innings active | POST ball: runs=4 | total_runs += 4 | High | FR-024 |
| TC-026 | Record six | Innings active | POST ball: runs=6 | total_runs += 6 | High | FR-024 |
| TC-027 | Undo last ball | Last ball not already corrected | DELETE /undo/1 | Ball deleted, innings totals reversed | High | FR-032 |
| TC-028 | Undo already-corrected ball | Last ball has is_correction=True | DELETE /undo/1 | 400 Bad Request: "Already corrected once" | High | FR-033 |
| TC-029 | Score on completed innings | Innings is_completed=True | POST ball | Error: "Innings is already completed" | High | FR-024 |
| TC-030 | Super over scoring (1 over max) | Super over innings active | Record 6 legal balls | innings.is_completed = True, total_overs = 1 | Medium | FR-021 |

#### 6.7.5 Real-time Update Tests

| TC-ID | Description | Precondition | Input | Expected Result | Priority | Maps To |
|-------|-------------|-------------|-------|-----------------|----------|---------|
| TC-031 | WebSocket connection | Match in LIVE status | Connect to /ws/live/1 | Connection accepted | High | FR-035 |
| TC-032 | WebSocket broadcast | 2 clients connected to match 1 | Record a ball on match 1 | Both clients receive JSON score update | High | FR-036 |
| TC-033 | REST live score | Match in LIVE status | GET /scoring/match/1/live | 200 OK, current score data | High | FR-037 |
| TC-034 | Full scorecard | Innings with balls recorded | GET /scoring/innings/1/scorecard | 200 OK, batting + bowling scorecard | High | FR-038 |

#### 6.7.6 Authentication Tests

| TC-ID | Description | Precondition | Input | Expected Result | Priority | Maps To |
|-------|-------------|-------------|-------|-----------------|----------|---------|
| TC-035 | User registration | No user with email | POST /api/user/register with name, email, password | 200 OK, user created, JWT cookie set | High | FR-044, FR-045 |
| TC-036 | OTP generation | User exists | POST /api/user/forgot-password with email | 200 OK, 6-digit OTP generated (5 min expiry) | High | FR-046, FR-047 |
| TC-037 | OTP verification (valid) | OTP generated for user | POST /api/user/verify-otp with correct OTP | 200 OK, JWT cookie set, OTP consumed | High | FR-049, FR-050 |
| TC-038 | OTP verification (expired) | OTP generated > 5 min ago | POST /api/user/verify-otp | 400 Bad Request | High | NFR-010 |
| TC-039 | OTP verification (wrong code) | OTP generated | POST /api/user/verify-otp with wrong OTP | 400 Bad Request | High | NFR-010 |
| TC-040 | Auto-create user on OTP login | No user with email | POST /api/user/forgot-password with new email | User auto-created, OTP sent | Medium | FR-051 |
| TC-041 | Profile update within limit | User has profile_edits < 5 | POST /api/user/profile with new batting_hand | 200 OK, profile_edits += 1 | Medium | FR-052, FR-053 |
| TC-042 | Profile update at limit | User has profile_edits = 5 | POST /api/user/profile with restricted field | 400: "Profile edit limit reached" | Medium | FR-053 |

#### 6.7.7 Data Persistence Tests

| TC-ID | Description | Precondition | Input | Expected Result | Priority | Maps To |
|-------|-------------|-------------|-------|-----------------|----------|---------|
| TC-043 | Data survives server restart | Players, teams, matches exist | Kill server → delete local DB → restart | All data intact (synced from Turso cloud) | High | NFR-004, NFR-006 |
| TC-044 | Data syncs on commit | New player created | Check Turso cloud | Record present in cloud database | High | NFR-005 |

#### 6.7.8 Frontend Tests

| TC-ID | Description | Precondition | Input | Expected Result | Priority | Maps To |
|-------|-------------|-------------|-------|-----------------|----------|---------|
| TC-045 | Admin panel loads | Server running | GET /admin | 200 OK, HTML with navigation | High | FR-071 |
| TC-046 | User app loads | Server running | GET /app | 200 OK, HTML with home page | High | FR-072 |
| TC-047 | Dark mode toggle | Light mode active | Click theme toggle button | data-theme="dark" set, persisted in localStorage | Medium | FR-073 |
| TC-048 | PWA installable | Service worker registered | Access from mobile Chrome | Install prompt appears | Medium | FR-074 |
| TC-049 | Static assets cached | Service worker active | Load page, go offline | CSS/JS/icons load from cache | Medium | FR-075 |
| TC-050 | HTML not cached | Service worker active | Log in as User A → log out → User B | User B sees own data, not User A's | High | NFR-012 |

---

## 7. Traceability Matrix

### 7.1 Requirements → Design → Implementation → Test

| Requirement | Design Section | Implementation Module | Test Cases |
|-------------|---------------|----------------------|------------|
| FR-001 | §4.3.2 Players Table, §4.4.1 Players API | app/routers/players.py | TC-001 |
| FR-002 | §4.4.1 Players API | app/routers/players.py | TC-002 |
| FR-003 | §4.4.1 Players API | app/routers/players.py | TC-003, TC-006 |
| FR-004 | §4.4.1 Players API | app/routers/players.py | TC-004 |
| FR-005 | §4.4.1 Players API | app/routers/players.py | TC-005 |
| FR-008 | §4.3.2 Teams Table, §4.4.1 Teams API | app/routers/teams.py | TC-007, TC-010 |
| FR-009 | §4.3.2 TeamPlayers Table | app/routers/teams.py | TC-008 |
| FR-010 | §4.4.1 Teams API | app/routers/teams.py | TC-009 |
| FR-014 | §4.3.2 Matches Table, §4.5.4 State Machine | app/routers/matches.py | TC-011 |
| FR-015 | §4.5.4 State Machine | app/routers/matches.py | TC-011 |
| FR-016 | §4.4.1 Matches API | app/routers/matches.py | TC-012 |
| FR-017 | §4.3.2 Innings Table | app/routers/matches.py | TC-012 |
| FR-018 | §4.5.4 State Machine | app/routers/matches.py | TC-013 |
| FR-019 | §4.4.1 Matches API | app/routers/matches.py | TC-014 |
| FR-020 | §4.5.1 Data Flow | app/routers/matches.py | TC-014 |
| FR-021 | §4.5.4 State Machine | app/routers/matches.py | TC-016, TC-030 |
| FR-024 | §4.3.2 Balls Table, §4.5.1 Data Flow | app/services/scoring.py | TC-017, TC-025, TC-026, TC-029 |
| FR-025 | §4.5.1 Data Flow | app/services/scoring.py | TC-018, TC-019 |
| FR-026 | §4.5.1 Data Flow | app/services/scoring.py | TC-018 |
| FR-027 | §4.5.1 Data Flow | app/services/scoring.py | TC-020 |
| FR-028 | §4.5.1 Data Flow | app/services/scoring.py | TC-017 |
| FR-029 | §4.5.1 Data Flow | app/services/scoring.py | TC-022, TC-023, TC-024 |
| FR-032 | §5.7 Undo System | app/routers/features.py | TC-027 |
| FR-033 | §5.7 Undo System | app/routers/features.py | TC-028 |
| FR-034 | §4.3.2 Balls Table | app/services/scoring.py | TC-021 |
| FR-035 | §4.4.2 WebSocket, §4.5.5 ConnectionManager | app/websocket/live_score.py | TC-031 |
| FR-036 | §4.5.5 ConnectionManager | app/websocket/live_score.py | TC-032 |
| FR-037 | §4.4.1 Scoring API | app/routers/scoring.py | TC-033 |
| FR-038 | §4.4.1 Scoring API | app/routers/scoring.py | TC-034 |
| FR-039 | §4.4.1 Stats API | app/services/stats.py | — |
| FR-040 | §4.4.1 Stats API | app/services/stats.py | — |
| FR-041 | §4.4.1 Stats API | app/services/records.py | — |
| FR-042 | §4.4.1 Stats API | app/services/rankings.py | — |
| FR-044 | §4.5.2 Auth Flow | app/routers/user_auth.py | TC-035 |
| FR-045 | §5.3 Auth Module | app/auth.py | TC-035 |
| FR-046 | §4.5.2 Auth Flow | app/routers/user_auth.py | TC-036, TC-037 |
| FR-047 | §5.3 Auth Module | app/auth.py | TC-036 |
| FR-049 | §5.3 Auth Module | app/auth.py | TC-037 |
| FR-050 | §5.3 Auth Module | app/auth.py | TC-037 |
| FR-051 | §4.5.2 Auth Flow | app/routers/user_auth.py | TC-040 |
| FR-052 | §4.4.1 User Auth API | app/routers/user_auth.py | TC-041 |
| FR-053 | §4.4.1 User Auth API | app/routers/user_auth.py | TC-042 |
| FR-056 | §5.5 Notification Service | app/services/notifications.py | TC-015 |
| FR-057 | §5.5 Notification Service | app/services/notifications.py | TC-015 |
| FR-071 | §4.4.1 External Interfaces | templates/base.html | TC-045 |
| FR-072 | §4.4.1 External Interfaces | templates/user/base.html | TC-046 |
| FR-073 | §5.9 Frontend JS, §5.10 CSS | static/js/app.js, static/css/style.css | TC-047 |
| FR-074 | §5.8 Service Worker | static/sw.js, static/manifest.json | TC-048 |
| FR-075 | §5.8 Service Worker | static/sw.js | TC-049, TC-050 |
| NFR-004 | §4.5.3 Turso Persistence | app/database.py | TC-043 |
| NFR-005 | §4.5.3 Turso Persistence | app/database.py | TC-044 |
| NFR-006 | §4.5.3 Turso Persistence | app/database.py | TC-043 |
| NFR-007 | §5.3 Auth Module | app/auth.py | TC-035 |
| NFR-008 | §5.3 Auth Module | app/auth.py | TC-037 |
| NFR-010 | §5.3 Auth Module | app/auth.py | TC-038, TC-039 |
| NFR-012 | §5.8 Service Worker | static/sw.js | TC-050 |
| NFR-019 | §5.1 Config Module | app/config.py | — |
| NFR-021 | §4.2.4 Layer Architecture | app/ directory structure | — |
| NFR-023 | §4.2 Architecture | app/main.py (FastAPI auto-docs) | — |

---

## 8. References

| Ref | Full Citation |
|-----|--------------|
| [1] | IEEE Computer Society. (2018). *IEEE Standard 29148-2018 — Systems and software engineering — Life cycle processes — Requirements engineering*. IEEE. |
| [2] | IEEE Computer Society. (2009). *IEEE Standard 1016-2009 — Systems design — Software design descriptions*. IEEE. |
| [3] | IEEE Computer Society. (2008). *IEEE Standard 829-2008 — Standard for Software and System Test Documentation*. IEEE. |
| [4] | Ramírez, S. (2018). *FastAPI framework, high performance, easy to learn*. https://fastapi.tiangolo.com/ |
| [5] | Bayer, M. (2012). *SQLAlchemy — The Database Toolkit for Python*. https://www.sqlalchemy.org/ |
| [6] | Turso. (2023). *Turso — SQLite for Production*. https://turso.tech/ |
| [7] | Pydantic. (2017). *Data validation using Python type annotations*. https://docs.pydantic.dev/ |
| [8] | Brevo (formerly Sendinblue). *Transactional Email API*. https://developers.brevo.com/ |
| [9] | Render. *Cloud Application Hosting for Developers*. https://render.com/docs |
| [10] | Fette, I. & Melnikov, A. (2011). *RFC 6455: The WebSocket Protocol*. IETF. https://www.rfc-editor.org/rfc/rfc6455 |
| [11] | OWASP Foundation. (2021). *OWASP Top 10 — 2021*. https://owasp.org/www-project-top-ten/ |

---

## 9. Appendices

### Appendix A: Environment Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./boxcric.db` |
| `SECRET_KEY` | JWT signing key | `boxcric-secret-change-in-production-2026` |
| `BREVO_API_KEY` | Brevo email API key | (empty — OTP logged to console) |
| `BREVO_SENDER_EMAIL` | Brevo sender email | (empty) |
| `RENDER_EXTERNAL_URL` | Render app URL for keep-alive | `https://boxcric.onrender.com` |

### Appendix B: Database URL Formats Supported

```
sqlite:///./boxcric.db                              # Local SQLite (default)
libsql://db-name.aws-us-west-2.turso.io?authToken=… # Turso cloud
postgresql://user:pass@host/db                       # PostgreSQL (Neon, etc.)
```

### Appendix C: Deployment Configuration

| Setting | Value |
|---------|-------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Python Version | 3.11.11 (pinned in runtime.txt) |
| Auto-deploy | Triggered on push to `main` branch |
| Keep-alive | Background task pings `/health` every 10 minutes |

### Appendix D: Future Enhancements

| Feature | Description |
|---------|-------------|
| Tournament/League mode | Points table, group stages, knockouts |
| Push notifications | Browser Push API for match events |
| Advanced analytics | Wagon wheel, pitch map, scoring zones |
| ML win predictor | Machine learning model for win probability |
| Native mobile app | React Native or Flutter wrapper |
| AI commentary | GPT-powered natural language commentary |
| Multi-language | Hindi, Telugu, Tamil support |
| Docker & CI/CD | Containerization and automated testing pipeline |

---

*Document ID: BOXCRIC-SRS-SDD-001 v1.0*
*Conforms to: IEEE 29148-2018, IEEE 1016-2009, IEEE 829-2008*
*Date: March 2026*
*Project: BOXcric — Cricket Match Management & Live Scoring Platform*
