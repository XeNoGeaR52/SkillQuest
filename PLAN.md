SkillQuest — Project Plan (complete)
1. Project summary (elevator pitch)

SkillQuest is a small service where users complete challenges to earn XP and badges. It demonstrates well-designed async REST APIs, relational modeling, background processing, authentication, tests, and deployment. Great demo: show a user completing a challenge and the app awarding XP and a badge with leaderboard and progress endpoints.

2. Tech stack & rationale

Backend: FastAPI (async, auto docs)

ORM: SQLAlchemy 1.4+ async with asyncpg driver (or SQLModel if you prefer simpler Pydantic/SQLAlchemy integration)

Migrations: Alembic (async-compatible config)

Database: PostgreSQL

Background tasks / jobs: Celery (with Redis broker) or RQ (simpler), for awarding XP, batch recalculations and external integrations

Cache / real-time: Redis (leaderboard cache, rate-limiting)

Auth: JWT (OAuth2 password flow) with refresh tokens; password hashing with passlib

Testing: pytest + pytest-asyncio, test PostgreSQL (or sqlite for unit tests), factory-boy for fixtures

Dev / Local: docker-compose for quick local deployment (postgres, redis, backend)

CI/CD: GitHub Actions; run tests, linters (ruff/flake8), build Docker image

Observability: Sentry (optional), Prometheus metrics + Grafana or simple logging

Optional frontend: minimal React or static HTML demo to show flows (not mandatory)

3. High-level architecture

FastAPI app (HTTP API)

PostgreSQL for persistent data

Redis for Celery broker + cache

Celery worker(s) for background tasks (award XP, issue badges, recalc stats)

Optional web frontend for demo

Docker-compose orchestrates local environment

GitHub Actions CI pipeline

Diagram (conceptual):

[User / Frontend] <--HTTPS--> [FastAPI] <---> [Postgres]
                                      |
                                      `--> [Redis] <--> [Celery Worker(s)]

4. Domain model & DB schema (ER)

Main entities:

User — players

Challenge — tasks to complete (type, xp, difficulty)

Attempt — a user’s attempt at a challenge (status, score, time)

UserXP or computed on-the-fly: total XP (cached in Redis or materialized)

Badge — rewards with conditions (e.g., 1000 XP, or complete 10 challenges)

UserBadge — awarded badges

Leaderboard — derived table/cache

Schema (fields, simplified)
User

id: UUID (PK)

username: str (unique)

email: str (unique)

password_hash: str

created_at: timestamp

profile (jsonb): optional

total_xp: int (denormalized, maintain via triggers/background jobs)

level: int (optional)

Challenge

id: UUID

title: str

description: text

xp: int

difficulty: enum (easy, medium, hard)

tags: text[] or jsonb

created_by: FK(User) optional

published: bool

Attempt

id: UUID

user_id: FK(User)

challenge_id: FK(Challenge)

status: enum (started, submitted, passed, failed)

score: int or float

xp_awarded: int

started_at, submitted_at: timestamps

metadata: jsonb (solution, runtime, etc.)

Badge

id: UUID

name: str

description: str

condition: jsonb (e.g. {"type":"xp","threshold":1000} or {"type":"streak","days":7})

icon_url: str optional

UserBadge

id: UUID

user_id: FK(User)

badge_id: FK(Badge)

awarded_at: timestamp

metadata: jsonb

Leaderboard (derived)

either maintain top N in Redis sorted set ZADD by total_xp or compute via SQL ORDER BY total_xp DESC LIMIT N

5. API design (key endpoints)

All endpoints return JSON, use standard HTTP status codes.

Auth

POST /auth/register — create user (body: username, email, password)

POST /auth/login — returns access_token, refresh_token

POST /auth/refresh — refresh access token

GET /auth/me — get current user

Challenges

GET /challenges — list with filters (difficulty, tags, pagination)

GET /challenges/{id} — details

POST /challenges — create (admin)

PUT /challenges/{id} — update (admin)

DELETE /challenges/{id} — delete (admin)

Attempts

POST /attempts — start an attempt (body: challenge_id); returns attempt id

POST /attempts/{attempt_id}/submit — submit results (body: solution, score)

On submit, server calculates if passed, xp_awarded, records Attempt, triggers background job to update user XP and badges

GET /attempts — list user attempts

GET /attempts/{id} — attempt details

Badges

GET /badges — list badges and conditions (admin creates)

GET /users/{user_id}/badges — user badges

Leaderboard & Progress

GET /leaderboard?limit=10 — top users

GET /users/{user_id}/progress — total_xp, level, next_level_xp, recent_attempts, badges

Admin / Stats

GET /admin/stats — total users, challenges, attempts, xp distributed (admin)

POST /admin/recalc-xp — trigger full recalculation (admin; background job)

6. Business logic highlights (what you demo / talk about)

XP awarding: xp_awarded computed using challenge.xp and attempt.score. Store xp_awarded in Attempt and add to User.total_xp in background job to avoid long request latency.

Badges: badges defined with flexible JSON conditions. Background worker evaluates badge conditions and creates UserBadge when met.

Leveling: simple level function: level = floor(sqrt(total_xp / 100)) or configurable mapping.

Leaderboard: maintain Redis sorted set (ZINCRBY on xp award) for instant top-N retrieval — talk about eventual consistency vs accuracy and trade-offs.

Security: rate limit attempt submissions to prevent spamming (Redis-based rate-limit).

7. Background jobs & async flow

Use Celery (Redis broker) or RQ:

award_xp_and_badges(attempt_id):

Load Attempt and Challenge

Compute xp_awarded

Update Attempt.xp_awarded, Attempt.status

Increment User.total_xp (atomic SQL UPDATE ... SET total_xp = total_xp + :x RETURNING total_xp)

ZADD leaderboard user_id total_xp in Redis

Evaluate badge conditions and create UserBadge if necessary

Emit websocket/notification (optional)

Use FastAPI BackgroundTasks only for non-critical small tasks; prefer Celery for reliability and visibility.

8. Folder / repo structure (suggested)
skillquest/
├─ app/
│  ├─ main.py
│  ├─ api/
│  │  ├─ v1/
│  │  │  ├─ auth.py
│  │  │  ├─ challenges.py
│  │  │  ├─ attempts.py
│  │  │  └─ badges.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ security.py
│  ├─ db/
│  │  ├─ base.py
│  │  ├─ models.py
│  │  ├─ session.py
│  ├─ services/
│  │  ├─ xp_service.py
│  │  ├─ badge_service.py
│  ├─ tasks/
│  │  ├─ worker.py
│  ├─ schemas/
│  │  ├─ pydantic schemas...
│  ├─ tests/
├─ alembic/
├─ docker-compose.yml
├─ Dockerfile
├─ requirements.txt
└─ README.md

9. Sample code snippets
Example async SQLAlchemy model (simplified)
# app/db/models.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = sa.Column(sa.String, unique=True, nullable=False)
    email = sa.Column(sa.String, unique=True, nullable=False)
    password_hash = sa.Column(sa.String, nullable=False)
    total_xp = sa.Column(sa.Integer, default=0, nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    profile = sa.Column(JSONB, nullable=True)

FastAPI route for submitting an attempt (synchronous view of flow)
# app/api/v1/attempts.py (sketch)
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.db.session import async_session
from app.services.xp_service import create_attempt_and_enqueue

router = APIRouter()

@router.post("/attempts")
async def create_attempt(payload: CreateAttemptSchema, current_user=Depends(get_current_user)):
    async with async_session() as session:
        attempt = await create_attempt_and_enqueue(session, user_id=current_user.id, challenge_id=payload.challenge_id)
        return attempt


create_attempt_and_enqueue creates an Attempt row and then enqueues award_xp_and_badges to Celery with the attempt ID.

10. Testing plan

Unit tests:

model serialization, level calculation, xp calculation functions, badge condition logic.

Integration tests:

API endpoints using httpx.AsyncClient and a test database (postgres test container or sqlite).

Test auth flows: register/login, protected endpoints return 401 when unauthenticated.

Test attempt submit -> background job stubbed or run synchronously in tests, verify XP and badges.

Test fixtures:

Use factory-boy to create test users, challenges, attempts.

CI:

Run tests in GitHub Actions.

Linting: ruff/flake8; type checks with mypy (optional).

11. CI/CD & deployment

CI (GitHub Actions):

On push/pr: run tests, lint, build Docker image, optionally push to registry on main.

Docker Compose (local):

Services: web (fastapi uvicorn), postgres, redis, worker (celery), pgadmin optional

Production:

Containerize and deploy to a provider (DigitalOcean App Platform, Heroku, AWS ECS, Fly.io).

Use managed Postgres + Redis.

Use environment variables (12-factor).

Set up migrations via Alembic in startup or CI/CD migration step.

Sample docker-compose.yml items:

services:
  web:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    env_file: .env
    ports: ["8000:8000"]
    depends_on: ["db", "redis"]
  db:
    image: postgres:15
    environment: ...
  redis:
    image: redis:7
  worker:
    build: .
    command: celery -A app.tasks.worker worker --loglevel=info
    depends_on: ["db","redis"]

12. Security & best practices

Hash passwords (bcrypt via passlib).

Secure JWT secret; set token expiration and refresh tokens.

Validate inputs via Pydantic models.

Sanitize stored metadata (no arbitrary code execution).

Rate limit endpoints that can be spammed (attempt submissions).

Use HTTPS in production, enable CORS only for allowed origins.

13. Observability & metrics (what to show in demo)

Track events: challenge_submitted, xp_awarded, badge_awarded.

Expose Prometheus metrics endpoint: http_requests_total, xp_awarded_total.

Logs: structured JSON logs; show a live log where you submit an attempt and the background worker logs awarding XP.

Provide simple dashboard: top-10 leaderboard, new users/day, total XP given.

14. Demo script for the interview (short, 6–8 minutes)

Intro (30s) — what SkillQuest is, architecture diagram.

Show schema (30s) — open models or ER diagram.

Open Swagger GET /challenges and POST /auth/register (30s).

Create/register user via /auth/register (30s).

Start & Submit Attempt:

POST /attempts -> POST /attempts/{id}/submit with a sample result (1 min).

Explain that submission enqueues background job; show worker logs awarding XP.

Show user progress /users/{id}/progress and /leaderboard to show updated XP and new badge (1 min).

Explain internals (how XP & badges are computed, why background jobs, caching, trade-offs) (1–2 min).

Wrap up: tests, CI, deployment steps, and next features (30s).

Tip: Have a small Postman collection or a few curl commands ready in a text file to paste/run.

15. Development roadmap (tasks, order — no durations)

Sequence of work (use as checklist):

Project repo & basic FastAPI app + config

DB session setup (async SQLAlchemy) + Alembic + initial migrations

Models: User, Challenge, Attempt, Badge, UserBadge

Auth system: register/login/JWT

CRUD endpoints for challenges and badges (admin)

Attempts endpoints: start & submit (synchronous flow that enqueues tasks)

Background worker: xp/badge logic + Redis leaderboard update

Leaderboard & user progress endpoints

Tests: unit + integration

Docker-compose setup (postgres, redis, web, worker)

CI pipeline (tests, lint)

Demo polish: sample data, README, Postman collection, demo script

Optional: minimal frontend or simple static UI

16. Example XP & level rules (show during interview)

XP for challenge = challenge.xp * (score / 100) (rounded)

Level formula (example): level = int(total_xp ** 0.5 / 10) + 1 (or a table)

Badge examples:

First Steps — complete first challenge (condition: {"type":"attempt_count","count":1})

Conqueror — total_xp >= 1000 ({"type":"xp","threshold":1000})

Streak — complete at least one challenge for 7 consecutive days ({"type":"consecutive_days","days":7})

17. Example queries to highlight SQL skills

Aggregate: SELECT user_id, SUM(xp_awarded) AS total_xp FROM attempts GROUP BY user_id ORDER BY total_xp DESC LIMIT 10;

Badge evaluation: query to check if user meets count-based badge:

SELECT COUNT(*) FROM attempts WHERE user_id = :u AND status='passed';


Use indexes on attempts(user_id), challenges(id), and users(total_xp) for performance.

18. Stretch goals / optional cool features

Real-time websocket notifications for XP/badge awards (FastAPI websockets).

Rate-limits & abuse detection per IP.

Social: follow users, compare progress with friends.

Challenge categories (time-limited events).

Admin analytics dashboard (recharts or Grafana).

Gamification hooks: streaks, daily quests, special events.

19. What to prepare before the interview

A local demo that runs with docker-compose up and seeded sample data.

A one-page slide (diagram + API endpoints + flow) for quick introduction.

A short recorded screencast or a Postman collection as backup if live demo fails.

Notes to explain tradeoffs (why async SQLAlchemy, why background workers, why Redis).

20. Ready-to-copy snippets & templates (bonus)

Below are three things you can copy into your repo quickly:

Docker-compose skeleton

version: "3.8"
services:
  web:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: skillquest
      POSTGRES_PASSWORD: password
      POSTGRES_DB: skillquest
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  worker:
    build: .
    command: celery -A app.tasks.worker worker --loglevel=info
    env_file: .env
    depends_on:
      - db
      - redis


Example shell commands for demo (curl)

# Register
curl -X POST http://localhost:8000/auth/register -d '{"username":"demo","email":"a@b.com","password":"secret"}' -H "Content-Type: application/json"

# Login -> save token
curl -X POST http://localhost:8000/auth/login -d '{"username":"demo","password":"secret"}' -H "Content-Type: application/json"

# List challenges
curl http://localhost:8000/challenges

# Start attempt
curl -X POST http://localhost:8000/attempts -H "Authorization: Bearer <token>" -d '{"challenge_id":"<id>"}'

# Submit attempt (simulate a pass)
curl -X POST http://localhost:8000/attempts/<attempt_id>/submit -H "Authorization: Bearer <token>" -d '{"score":95,"solution":"..."}'

21. What I would present in the interview (scripted bullets)

“What” and “why” (20s)

Architecture slide (20s)

Show schema and sample model (30s)

Live API demo: register, start attempt, submit (2 min)

Show worker logs awarding XP + leaderboard update (1 min)

Explain tradeoffs & next steps (1 min)

Offer to walk through code after (30s)

22. Final checklist (pre-interview)

 Repo with README and run instructions (docker-compose up)

 Seed script that creates demo users, challenges, badges

 Postman/curl demo script

 One-page slide / diagram

 Tests passing in CI

 Demo script practiced