from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List
from app.db.models import DifficultyEnum


class ChallengeBase(BaseModel):
    """Base challenge schema."""
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    xp: int = Field(..., ge=1)
    difficulty: DifficultyEnum
    tags: List[str] | None = None


class ChallengeCreate(ChallengeBase):
    """Schema for creating a challenge."""
    published: bool = True


class ChallengeUpdate(BaseModel):
    """Schema for updating a challenge."""
    title: str | None = None
    description: str | None = None
    xp: int | None = Field(None, ge=1)
    difficulty: DifficultyEnum | None = None
    tags: List[str] | None = None
    published: bool | None = None


class ChallengeResponse(ChallengeBase):
    """Schema for challenge response."""
    id: UUID
    created_by: UUID | None = None
    published: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ChallengeListParams(BaseModel):
    """Query parameters for listing challenges."""
    difficulty: DifficultyEnum | None = None
    tags: List[str] | None = None
    skip: int = Field(0, ge=0)
    limit: int = Field(10, ge=1, le=100)
