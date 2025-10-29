from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.deps import get_current_active_user
from app.db.models import Badge, User, UserBadge
from app.db.session import get_db
from app.schemas.badge import BadgeCreate, BadgeResponse, UserBadgeResponse

router = APIRouter()


@router.get("/", response_model=List[BadgeResponse])
async def list_badges(
    db: AsyncSession = Depends(get_db)
):
    """
    List all available badges and their conditions.
    """
    result = await db.execute(select(Badge).order_by(Badge.created_at))
    badges = result.scalars().all()
    return badges


@router.post("/", response_model=BadgeResponse, status_code=status.HTTP_201_CREATED)
async def create_badge(
    badge_data: BadgeCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new badge (authenticated users only - in production, restrict to admins).

    Condition types supported:
    - XP threshold: {"type": "xp", "threshold": 1000}
    - Attempt count: {"type": "attempt_count", "count": 10, "status": "passed"}
    - Consecutive days: {"type": "consecutive_days", "days": 7}

    - **name**: Badge name (unique)
    - **description**: Badge description
    - **condition**: JSON condition for earning the badge
    - **icon_url**: Optional URL to badge icon
    """
    # Check if badge name already exists
    result = await db.execute(select(Badge).where(Badge.name == badge_data.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Badge with this name already exists"
        )

    new_badge = Badge(
        name=badge_data.name,
        description=badge_data.description,
        condition=badge_data.condition,
        icon_url=badge_data.icon_url
    )

    db.add(new_badge)
    await db.commit()
    await db.refresh(new_badge)

    return new_badge


@router.get("/users/{user_id}", response_model=List[UserBadgeResponse])
async def get_user_badges(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all badges earned by a specific user.
    """
    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get user's badges with badge details
    result = await db.execute(
        select(UserBadge)
        .options(joinedload(UserBadge.badge))
        .where(UserBadge.user_id == user_id)
        .order_by(UserBadge.awarded_at.desc())
    )
    user_badges = result.scalars().all()

    # Transform to response format
    response = []
    for user_badge in user_badges:
        response.append({
            "id": user_badge.id,
            "badge_id": user_badge.badge_id,
            "badge_name": user_badge.badge.name,
            "badge_description": user_badge.badge.description,
            "badge_icon_url": user_badge.badge.icon_url,
            "awarded_at": user_badge.awarded_at,
            "badge_metadata": user_badge.badge_metadata
        })

    return response


@router.get("/me", response_model=List[UserBadgeResponse])
async def get_my_badges(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all badges earned by the current user.
    """
    # Get user's badges with badge details
    result = await db.execute(
        select(UserBadge)
        .options(joinedload(UserBadge.badge))
        .where(UserBadge.user_id == current_user.id)
        .order_by(UserBadge.awarded_at.desc())
    )
    user_badges = result.scalars().all()

    # Transform to response format
    response = []
    for user_badge in user_badges:
        response.append({
            "id": user_badge.id,
            "badge_id": user_badge.badge_id,
            "badge_name": user_badge.badge.name,
            "badge_description": user_badge.badge.description,
            "badge_icon_url": user_badge.badge.icon_url,
            "awarded_at": user_badge.awarded_at,
            "badge_metadata": user_badge.badge_metadata
        })

    return response
