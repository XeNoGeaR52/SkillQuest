from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class LeaderboardEntry(BaseModel):
    """Schema for a leaderboard entry."""
    user_id: UUID
    username: str
    total_xp: int
    level: int
    rank: int


class LeaderboardResponse(BaseModel):
    """Schema for leaderboard response."""
    entries: List[LeaderboardEntry]
    total_count: int


class UserProgress(BaseModel):
    """Schema for user progress/stats."""
    user_id: UUID
    username: str
    total_xp: int
    level: int
    next_level_xp: int
    total_challenges_completed: int
    total_badges: int
    recent_attempts: List[dict] = Field(default_factory=list)
