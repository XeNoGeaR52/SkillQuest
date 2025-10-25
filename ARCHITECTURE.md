# SkillQuest - Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client / User                           │
│                    (Browser, Mobile App, CLI)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                        FastAPI Server                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Routers (auth, challenges, attempts, badges, board)     │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  Dependencies (JWT auth, DB session)                     │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  Services (XP calc, Badge eval, Redis ops)               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────┬─────────────────────┬──────────────────────┬──┘
                  │                     │                      │
        ┌─────────▼─────────┐ ┌────────▼─────────┐ ┌─────────▼────────┐
        │   PostgreSQL      │ │      Redis       │ │  Celery Worker   │
        │                   │ │                  │ │                  │
        │ • Users           │ │ • Leaderboard    │ │ • Award XP       │
        │ • Challenges      │ │ • Task Queue     │ │ • Check Badges   │
        │ • Attempts        │ │ • Session Cache  │ │ • Update Redis   │
        │ • Badges          │ │                  │ │                  │
        │ • UserBadges      │ │                  │ │                  │
        └───────────────────┘ └──────────────────┘ └──────────────────┘
```

## Request Flow

### Typical Request Flow (Attempt Submission)

```
1. User submits attempt
   ↓
2. FastAPI validates JWT token
   ↓
3. API updates attempt status to "submitted"
   ↓
4. API enqueues Celery task
   ↓
5. API returns response (fast!)
   ↓
6. [Async] Celery worker processes task:
   a. Load attempt & challenge
   b. Calculate XP based on score
   c. Update user's total_xp
   d. Recalculate user level
   e. Update Redis leaderboard
   f. Evaluate badge conditions
   g. Award any earned badges
   ↓
7. User can query progress to see updates
```

## Data Model

```
┌──────────────┐
│     User     │
├──────────────┤
│ id (PK)      │
│ username     │◄──────────┐
│ email        │           │
│ password_hash│           │
│ total_xp     │           │
│ level        │           │
│ created_at   │           │
└──────────────┘           │
       │                   │
       │ 1:N               │ 1:N
       │                   │
┌──────▼────────┐    ┌─────┴──────────┐
│   Attempt     │    │   UserBadge    │
├───────────────┤    ├────────────────┤
│ id (PK)       │    │ id (PK)        │
│ user_id (FK)  │    │ user_id (FK)   │
│ challenge_id  │    │ badge_id (FK)  │
│ status        │    │ awarded_at     │
│ score         │    │ metadata       │
│ xp_awarded    │    └────────┬───────┘
│ started_at    │             │
│ submitted_at  │             │ N:1
└───────┬───────┘             │
        │                     │
        │ N:1           ┌─────▼─────────┐
        │               │     Badge     │
┌───────▼──────┐        ├───────────────┤
│  Challenge   │        │ id (PK)       │
├──────────────┤        │ name          │
│ id (PK)      │        │ description   │
│ title        │        │ condition     │
│ description  │        │ icon_url      │
│ xp           │        │ created_at    │
│ difficulty   │        └───────────────┘
│ tags         │
│ published    │
│ created_by   │
│ created_at   │
└──────────────┘
```

## Component Responsibilities

### FastAPI Application (app/main.py)
- HTTP server
- Request routing
- CORS middleware
- Dependency injection

### API Routers (app/api/v1/)
- **auth.py**: Registration, login, token management
- **challenges.py**: CRUD for challenges
- **attempts.py**: Start/submit attempts
- **badges.py**: Badge management
- **leaderboard.py**: Rankings and user progress

### Core Services (app/services/)
- **xp_service.py**: XP calculations, level formulas
- **badge_service.py**: Badge condition evaluation
- **redis_service.py**: Leaderboard operations

### Background Workers (app/tasks/)
- **worker.py**: Celery task definitions
- Processes XP awards asynchronously
- Updates leaderboard cache
- Evaluates and awards badges

### Database Layer (app/db/)
- **models.py**: SQLAlchemy ORM models
- **session.py**: Async session management
- **base.py**: Declarative base

## Authentication Flow

```
Registration:
  Client → POST /auth/register
       → Hash password (bcrypt)
       → Store user in DB
       → Return user object

Login:
  Client → POST /auth/login
       → Verify password
       → Generate JWT access token (30 min)
       → Generate JWT refresh token (7 days)
       → Return both tokens

Protected Endpoint:
  Client → GET /attempts (with Bearer token)
       → Decode JWT
       → Validate signature & expiry
       → Extract user_id from token
       → Load user from DB
       → Execute endpoint logic
       → Return response

Token Refresh:
  Client → POST /auth/refresh (with refresh token)
       → Validate refresh token
       → Generate new access token
       → Generate new refresh token
       → Return both tokens
```

## XP & Leveling System

### XP Calculation
```python
xp_awarded = challenge_xp × (score / 100)

Example:
  Challenge: 100 XP
  Score: 85%
  Awarded: 100 × 0.85 = 85 XP
```

### Level Calculation
```python
level = floor(sqrt(total_xp / 100)) + 1

Examples:
  0 XP    → Level 1
  100 XP  → Level 2
  400 XP  → Level 3
  900 XP  → Level 4
  1600 XP → Level 5
```

### Next Level XP
```python
next_level_xp = ((current_level) ^ 2) × 100

Examples:
  Level 1 → Need 100 XP for Level 2
  Level 2 → Need 400 XP for Level 3
  Level 3 → Need 900 XP for Level 4
```

## Badge System

### Badge Condition Types

1. **XP Threshold**
```json
{
  "type": "xp",
  "threshold": 1000
}
```
Award when user reaches 1000+ total XP.

2. **Attempt Count**
```json
{
  "type": "attempt_count",
  "count": 10,
  "status": "passed"
}
```
Award when user passes 10+ challenges.

3. **Consecutive Days**
```json
{
  "type": "consecutive_days",
  "days": 7
}
```
Award when user completes challenges on 7 different days.

### Badge Evaluation Flow
```
Trigger: Attempt marked as "passed"
  ↓
1. Get all badges from DB
2. Get user's existing badges
3. Filter out already-earned badges
4. For each remaining badge:
   a. Read condition from badge.condition JSON
   b. Query database for relevant data
   c. Evaluate condition (>=, ==, etc.)
   d. If met, create UserBadge record
5. Commit all new badges to DB
```

## Leaderboard Implementation

### Redis Sorted Set
```
Key: "leaderboard"
Score: total_xp
Member: user_id

Operations:
  ZADD leaderboard user_id total_xp    # Update/add
  ZREVRANGE leaderboard 0 9            # Top 10
  ZREVRANK leaderboard user_id         # Get rank
```

### Why Redis?
- **Fast**: O(log N) for updates and queries
- **Atomic**: Single command updates
- **Sorted**: Maintains order automatically
- **Scalable**: Handles millions of users

### Alternative (SQL)
```sql
SELECT * FROM users
ORDER BY total_xp DESC
LIMIT 10;
```
- **Slower**: O(N log N) for each query
- **Locks**: Table-level sorting locks
- **Resources**: CPU-intensive on large datasets

## Background Processing

### Why Celery?
- **Reliability**: Tasks are persisted
- **Retries**: Automatic retry on failure
- **Visibility**: Can monitor task status
- **Scaling**: Add more workers easily
- **Priority**: Task prioritization

### Task Flow
```
1. API enqueues task
   celery.send_task('award_xp_and_badges', args=[attempt_id])

2. Redis stores task in queue

3. Worker picks up task
   worker.award_xp_and_badges(attempt_id)

4. Worker executes:
   - Database updates
   - XP calculation
   - Badge checks
   - Redis updates

5. Task marked complete or failed
```

## Caching Strategy

### What's Cached?
- **Leaderboard**: Full sorted set in Redis
- **User Ranks**: Computed on-demand from sorted set

### Cache Invalidation
- **Leaderboard**: Updated on every XP award (eventual consistency)
- **No TTL**: Data doesn't expire (always current)

### Trade-offs
- **Pro**: Instant leaderboard queries
- **Pro**: No database load for rankings
- **Con**: Slight delay between submission and leaderboard update (1-2s)
- **Con**: Need to rebuild if Redis crashes (rare)

## Security Considerations

### Implemented
✅ Password hashing (bcrypt)
✅ JWT with expiration
✅ Token type validation (access vs refresh)
✅ Input validation (Pydantic)
✅ SQL injection prevention (ORM)
✅ CORS configuration

### Production Additions
- [ ] Rate limiting (by IP or user)
- [ ] Token blacklist (for logout)
- [ ] HTTPS enforcement
- [ ] Request size limits
- [ ] IP whitelisting for admin endpoints
- [ ] Audit logging
- [ ] Secrets management (Vault, AWS Secrets Manager)

## Scalability

### Horizontal Scaling
```
                    Load Balancer
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   FastAPI 1        FastAPI 2        FastAPI 3
        │                │                │
        └────────────────┼────────────────┘
                         │
                    PostgreSQL
                    (Read Replicas)
                         │
                      Redis
                    (Sentinel/Cluster)
                         │
                 ┌───────┴───────┐
            Worker 1         Worker 2
```

### Bottleneck Analysis
- **Database**: Add read replicas for queries
- **Redis**: Use Redis Cluster for sharding
- **Workers**: Add more Celery workers
- **API**: Add more FastAPI instances behind LB

## Monitoring & Observability

### Current
- Health check endpoint (`/health`)
- Structured logging
- Worker logs

### Production Additions
- **Metrics**: Prometheus + Grafana
- **Tracing**: OpenTelemetry
- **Error Tracking**: Sentry
- **APM**: DataDog or New Relic
- **Alerts**: PagerDuty integration

## Deployment Options

### Option 1: Docker Compose (Simple)
```bash
docker-compose up --build
```
Good for: Development, small deployments

### Option 2: Kubernetes (Scalable)
```yaml
Deployments:
  - web (FastAPI)
  - worker (Celery)
Services:
  - PostgreSQL (StatefulSet)
  - Redis (StatefulSet)
Ingress:
  - HTTPS termination
  - Load balancing
```
Good for: Production, auto-scaling

### Option 3: Platform-as-a-Service
- **Heroku**: Easy deployment
- **Fly.io**: Edge deployment
- **Railway**: Simple scaling
- **DigitalOcean App Platform**: Managed services

Good for: MVP, rapid iteration

## Performance Characteristics

| Operation | Complexity | Response Time |
|-----------|-----------|---------------|
| Login | O(1) | 50-100ms |
| List Challenges | O(N) | 20-50ms |
| Submit Attempt | O(1) | 30-60ms |
| Award XP (bg) | O(1) | 100-500ms |
| Leaderboard | O(log N) | 10-30ms |
| User Progress | O(1) | 20-40ms |
| Badge Evaluation | O(B) | 50-200ms |

B = number of badges, N = result set size

## Testing Strategy

### Unit Tests
- XP calculation functions
- Level formulas
- Badge condition logic
- Pure business logic

### Integration Tests
- API endpoints
- Authentication flow
- Database operations
- Redis interactions

### E2E Tests (Future)
- Complete user workflows
- Background job processing
- Multi-user scenarios

## Development Workflow

1. **Local Development**
   ```bash
   docker-compose up
   # Code changes auto-reload
   ```

2. **Run Tests**
   ```bash
   pytest app/tests/
   ```

3. **Create Migration**
   ```bash
   alembic revision --autogenerate -m "description"
   alembic upgrade head
   ```

4. **Lint Code**
   ```bash
   ruff check app/
   ```

5. **Push Changes**
   ```bash
   git push origin feature-branch
   # CI runs automatically
   ```

This architecture provides a solid foundation for a production-grade gamification platform with clear separation of concerns, scalability, and maintainability.
