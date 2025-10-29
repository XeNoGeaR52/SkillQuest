from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class BadgeBase(BaseModel):
    """Base badge schema."""
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10)
    condition: dict[str, Any]
    icon_url: str | None = None


class BadgeCreate(BadgeBase):
    """Schema for creating a badge."""
    pass


class BadgeResponse(BadgeBase):
    """Schema for badge response."""
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class UserBadgeResponse(BaseModel):
    """Schema for user's earned badge."""
    id: UUID
    badge_id: UUID
    badge_name: str
    badge_description: str
    badge_icon_url: str | None
    awarded_at: datetime
    badge_metadata: dict[str, Any] | None

    model_config = {"from_attributes": True}
