# SkillQuest

A gamification platform where users complete coding challenges to earn XP and badges. Built with FastAPI, PostgreSQL, Redis, and Celery to demonstrate production-ready async REST APIs, background processing, and caching strategies.

## Features

- **User Authentication**: JWT-based auth with access and refresh tokens
- **Challenge Management**: CRUD operations for coding challenges
- **Attempt Tracking**: Submit challenge attempts and receive scores
- **XP System**: Automatic XP calculation and level progression
- **Badge System**: Dynamic badge awards based on configurable conditions
- **Leaderboard**: Real-time leaderboard using Redis sorted sets
- **Background Processing**: Celery workers for async XP/badge awards
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Tech Stack

- **Backend**: FastAPI (async)
- **Database**: PostgreSQL with async SQLAlchemy
- **Cache/Queue**: Redis (leaderboard cache + Celery broker)
- **Background Jobs**: Celery
- **Migrations**: Alembic
- **Authentication**: JWT with OAuth2
- **Testing**: pytest with pytest-asyncio
- **Containerization**: Docker + Docker Compose

## Architecture

```
[Client] <--HTTPS--> [FastAPI] <---> [PostgreSQL]
                         |
                         `--> [Redis] <--> [Celery Worker(s)]
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd SkillQuest
cp .env.example .env
```

### 2. Start Services

```bash
docker-compose up --build
```

This will start:
- **Web** (FastAPI): http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Celery Worker**: Background task processor

### 3. Run Migrations

```bash
# In a new terminal
docker-compose exec web alembic upgrade head
```

### 4. Seed Database

```bash
docker-compose exec web python -m scripts.seed_data
```

### 5. Access API

- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Sample Credentials

After seeding, you can login with:
- Username: `alice` | Password: `password123`
- Username: `bob` | Password: `password123`
- Username: `charlie` | Password: `password123`

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login (get tokens)
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user profile

### Challenges
- `GET /challenges` - List challenges (with filters)
- `GET /challenges/{id}` - Get challenge details
- `POST /challenges` - Create challenge (auth required)
- `PUT /challenges/{id}` - Update challenge (creator only)
- `DELETE /challenges/{id}` - Delete challenge (creator only)

### Attempts
- `POST /attempts` - Start a challenge attempt
- `POST /attempts/{id}/submit` - Submit attempt with score
- `GET /attempts` - List user's attempts
- `GET /attempts/{id}` - Get attempt details

### Badges
- `GET /badges` - List all badges
- `POST /badges` - Create badge (auth required)
- `GET /badges/users/{user_id}` - Get user's badges
- `GET /badges/me` - Get current user's badges

### Leaderboard & Progress
- `GET /leaderboard` - Get top users
- `GET /leaderboard/users/{user_id}/progress` - Get user progress/stats

## Demo Workflow

### 1. Register a User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo",
    "email": "demo@example.com",
    "password": "password123"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=password123"
```

Save the `access_token` from the response.

### 3. List Challenges

```bash
curl http://localhost:8000/challenges
```

### 4. Start an Attempt

```bash
curl -X POST http://localhost:8000/attempts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"challenge_id": "CHALLENGE_UUID"}'
```

### 5. Submit Attempt

```bash
curl -X POST http://localhost:8000/attempts/ATTEMPT_ID/submit \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 95,
    "solution": "print(\"Hello, World!\")"
  }'
```

The background worker will:
1. Calculate XP based on score
2. Update user's total XP and level
3. Update leaderboard in Redis
4. Check and award any earned badges

### 6. Check Progress

```bash
curl http://localhost:8000/leaderboard/users/USER_ID/progress
```

### 7. View Leaderboard

```bash
curl http://localhost:8000/leaderboard?limit=10
```

## Development

### Local Setup (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your local database/Redis URLs

# Run migrations
alembic upgrade head

# Seed database
python -m scripts.seed_data

# Start FastAPI
uvicorn app.main:app --reload

# In another terminal, start Celery worker
celery -A app.tasks.worker worker --loglevel=info
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Business Logic Highlights

### XP Calculation

```python
xp_awarded = challenge_xp * (score / 100)
```

For example, a challenge worth 100 XP with a score of 85% awards 85 XP.

### Level Formula

```python
level = floor(sqrt(total_xp / 100)) + 1
```

XP requirements:
- Level 1: 0 XP
- Level 2: 100 XP
- Level 3: 400 XP
- Level 4: 900 XP
- Level 5: 1600 XP

### Badge Conditions

Badges support flexible JSON conditions:

```json
// XP threshold
{"type": "xp", "threshold": 1000}

// Attempt count
{"type": "attempt_count", "count": 10, "status": "passed"}

// Consecutive days (simplified)
{"type": "consecutive_days", "days": 7}
```

### Leaderboard Caching

Uses Redis sorted sets for O(log N) performance:
```python
ZADD leaderboard user_id total_xp  # Update
ZREVRANGE leaderboard 0 9          # Top 10
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py
```

## Project Structure

```
SkillQuest/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── challenges.py
│   │       ├── attempts.py
│   │       ├── badges.py
│   │       └── leaderboard.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── deps.py
│   ├── db/
│   │   ├── base.py
│   │   ├── models.py
│   │   └── session.py
│   ├── services/
│   │   ├── xp_service.py
│   │   ├── badge_service.py
│   │   └── redis_service.py
│   ├── tasks/
│   │   └── worker.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── challenge.py
│   │   ├── attempt.py
│   │   ├── badge.py
│   │   └── leaderboard.py
│   ├── tests/
│   └── main.py
├── alembic/
├── scripts/
│   └── seed_data.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Design Decisions & Trade-offs

### Async SQLAlchemy
- **Why**: Non-blocking I/O for better concurrency under load
- **Trade-off**: More complex than sync, requires async/await throughout

### Celery for Background Jobs
- **Why**: Reliable, visible, retryable task execution
- **Trade-off**: Additional service to manage vs FastAPI BackgroundTasks
- **Alternative**: Could use FastAPI's `BackgroundTasks` for simpler setups

### Redis Leaderboard Cache
- **Why**: O(log N) sorted set operations, instant top-N queries
- **Trade-off**: Eventual consistency (brief delay after XP update)
- **Benefit**: Avoids expensive `ORDER BY total_xp DESC` queries on every request

### JWT Auth
- **Why**: Stateless, scalable authentication
- **Trade-off**: Can't revoke tokens before expiry (would need token blacklist)

## CI/CD

The project includes a GitHub Actions workflow that:
1. Runs linting (ruff)
2. Runs tests with coverage
3. Builds Docker image
4. Optionally pushes to registry

## Future Enhancements

- [ ] WebSocket notifications for real-time XP/badge awards
- [ ] Rate limiting for attempt submissions
- [ ] Admin dashboard
- [ ] Challenge categories and time-limited events
- [ ] Social features (follow users, compare progress)
- [ ] More sophisticated streak tracking
- [ ] Prometheus metrics and Grafana dashboards

## License

MIT
