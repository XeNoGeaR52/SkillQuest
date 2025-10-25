from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Any
from app.db.models import AttemptStatusEnum


class AttemptCreate(BaseModel):
    """Schema for creating/starting an attempt."""
    challenge_id: UUID


class AttemptSubmit(BaseModel):
    """Schema for submitting an attempt."""
    score: float = Field(..., ge=0, le=100)
    solution: str | None = None
    metadata: dict[str, Any] | None = None


class AttemptResponse(BaseModel):
    """Schema for attempt response."""
    id: UUID
    user_id: UUID
    challenge_id: UUID
    status: AttemptStatusEnum
    score: float | None
    xp_awarded: int
    started_at: datetime
    submitted_at: datetime | None
    attempt_metadata: dict[str, Any] | None

    model_config = {"from_attributes": True}


class AttemptWithChallenge(AttemptResponse):
    """Attempt response with challenge details."""
    challenge_title: str
    challenge_xp: int
