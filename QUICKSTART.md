# SkillQuest - Quick Start Guide

## Get Up and Running in 5 Minutes

### 1. Start the Application

```bash
# Start all services (web, db, redis, worker)
docker-compose up --build
```

Wait for the services to start. You should see logs from all containers.

### 2. Run Database Migrations

In a new terminal:

```bash
# Create database tables
docker-compose exec web alembic upgrade head
```

### 3. Seed Sample Data

```bash
# Add sample challenges, badges, and users
docker-compose exec web python -m scripts.seed_data
```

### 4. Access the Application

Open your browser to:
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 5. Run the Demo Script

```bash
# Make sure jq is installed (for JSON formatting)
# Ubuntu/Debian: sudo apt-get install jq
# macOS: brew install jq

# Run the demo
./demo_script.sh
```

This script will:
1. Register a new user
2. Login and get tokens
3. List challenges
4. Start and submit a challenge attempt
5. Show XP/badge awards
6. Display the leaderboard

## Testing with Sample Users

The seed script creates three users:

| Username | Password | Email |
|----------|----------|-------|
| alice | password123 | alice@example.com |
| bob | password123 | bob@example.com |
| charlie | password123 | charlie@example.com |

## Using the API Manually

### 1. Register a New User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "yourname",
    "email": "your@email.com",
    "password": "yourpassword"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=yourname&password=yourpassword"
```

Save the `access_token` from the response.

### 3. View Challenges

```bash
curl http://localhost:8000/challenges
```

### 4. Start an Attempt

```bash
curl -X POST http://localhost:8000/attempts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"challenge_id": "CHALLENGE_UUID_FROM_STEP_3"}'
```

### 5. Submit Your Attempt

```bash
curl -X POST http://localhost:8000/attempts/ATTEMPT_ID/submit \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 95,
    "solution": "your code here"
  }'
```

### 6. Check Your Progress

```bash
curl http://localhost:8000/leaderboard/users/YOUR_USER_ID/progress
```

## What Happens When You Submit an Attempt?

1. **API receives submission** → Updates attempt status to "submitted"
2. **Celery task queued** → Background worker picks up the task
3. **Worker calculates XP** → Based on challenge XP and your score
4. **User XP updated** → Total XP increased, level recalculated
5. **Leaderboard updated** → Redis sorted set updated instantly
6. **Badges checked** → Worker evaluates badge conditions
7. **Badges awarded** → Any newly earned badges are recorded

You can see the worker logs with:
```bash
docker-compose logs -f worker
```

## Monitoring Services

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f db
```

### Check Service Health

```bash
# Web API
curl http://localhost:8000/health

# PostgreSQL
docker-compose exec db psql -U skillquest -c "SELECT 1"

# Redis
docker-compose exec redis redis-cli ping
```

## Stopping the Application

```bash
# Stop services (keep data)
docker-compose stop

# Stop and remove containers (keep volumes)
docker-compose down

# Stop and remove everything including data
docker-compose down -v
```

## Troubleshooting

### Database Connection Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d db
sleep 5
docker-compose exec web alembic upgrade head
docker-compose exec web python -m scripts.seed_data
```

### Worker Not Processing Tasks

```bash
# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker
```

### Port Already in Use

If port 8000, 5432, or 6379 is already in use, edit `docker-compose.yml` to change the port mappings.

## Next Steps

- Explore the [full README](README.md) for architecture details
- Check out the [API documentation](http://localhost:8000/docs)
- Run tests: `docker-compose exec web pytest`
- Create your own challenges via the API
- Build a frontend to interact with the API

Happy coding!
