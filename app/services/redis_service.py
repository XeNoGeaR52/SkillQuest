import redis.asyncio as aioredis
from app.core.config import settings
from typing import List, Tuple
from uuid import UUID

# Redis client instance
redis_client = None


async def get_redis():
    """Get Redis client instance."""
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


async def update_leaderboard(user_id: UUID, total_xp: int):
    """
    Update user's position in the leaderboard.

    Args:
        user_id: User's UUID
        total_xp: User's total XP
    """
    redis = await get_redis()
    await redis.zadd("leaderboard", {str(user_id): total_xp})


async def get_leaderboard(limit: int = 10) -> List[Tuple[str, float]]:
    """
    Get top users from leaderboard.

    Args:
        limit: Number of top users to retrieve

    Returns:
        List of (user_id, score) tuples
    """
    redis = await get_redis()
    # ZREVRANGE returns highest scores first
    results = await redis.zrevrange("leaderboard", 0, limit - 1, withscores=True)
    return results


async def get_user_rank(user_id: UUID) -> int | None:
    """
    Get user's rank in the leaderboard.

    Args:
        user_id: User's UUID

    Returns:
        User's rank (1-indexed) or None if not found
    """
    redis = await get_redis()
    rank = await redis.zrevrank("leaderboard", str(user_id))
    if rank is not None:
        return rank + 1  # Convert to 1-indexed
    return None


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
