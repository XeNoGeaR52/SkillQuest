from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Attempt, AttemptStatusEnum, User, UserBadge
from app.db.session import get_db
from app.schemas.leaderboard import LeaderboardEntry, LeaderboardResponse, UserProgress
from app.services.redis_service import get_leaderboard
from app.services.xp_service import calculate_next_level_xp

router = APIRouter()


@router.get("/", response_model=LeaderboardResponse)
async def get_leaderboard_endpoint(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the top users on the leaderboard.

    This endpoint returns cached leaderboard data from Redis for fast performance.

    - **limit**: Number of top users to return (1-100, default: 10)
    """
    # Get leaderboard from Redis
    leaderboard_data = await get_leaderboard(limit)

    # Get user details from database
    user_ids = [UUID(user_id) for user_id, _ in leaderboard_data]

    result = await db.execute(
        select(User).where(User.id.in_(user_ids))
    )
    users_dict = {user.id: user for user in result.scalars().all()}

    # Build response
    entries = []
    for rank, (user_id_str, xp) in enumerate(leaderboard_data, start=1):
        user_id = UUID(user_id_str)
        user = users_dict.get(user_id)

        if user:
            entries.append(LeaderboardEntry(
                user_id=user.id,
                username=user.username,
                total_xp=int(xp),
                level=user.level,
                rank=rank
            ))

    return LeaderboardResponse(
        entries=entries,
        total_count=len(entries)
    )


@router.get("/users/{user_id}/progress", response_model=UserProgress)
async def get_user_progress(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed progress and statistics for a specific user.

    - **user_id**: UUID of the user
    """
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Count completed challenges
    result = await db.execute(
        select(func.count(Attempt.id))
        .where(Attempt.user_id == user_id)
        .where(Attempt.status == AttemptStatusEnum.PASSED)
    )
    total_challenges_completed = result.scalar() or 0

    # Count badges
    result = await db.execute(
        select(func.count(UserBadge.id))
        .where(UserBadge.user_id == user_id)
    )
    total_badges = result.scalar() or 0

    # Get recent attempts
    result = await db.execute(
        select(Attempt)
        .where(Attempt.user_id == user_id)
        .order_by(Attempt.started_at.desc())
        .limit(5)
    )
    recent_attempts = result.scalars().all()

    recent_attempts_data = [
        {
            "id": str(attempt.id),
            "challenge_id": str(attempt.challenge_id),
            "status": attempt.status.value,
            "score": attempt.score,
            "xp_awarded": attempt.xp_awarded,
            "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None
        }
        for attempt in recent_attempts
    ]

    # Calculate next level XP
    next_level_xp = calculate_next_level_xp(user.level)

    return UserProgress(
        user_id=user.id,
        username=user.username,
        total_xp=user.total_xp,
        level=user.level,
        next_level_xp=next_level_xp,
        total_challenges_completed=total_challenges_completed,
        total_badges=total_badges,
        recent_attempts=recent_attempts_data
    )
