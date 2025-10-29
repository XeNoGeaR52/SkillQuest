from datetime import datetime
from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Attempt, AttemptStatusEnum, Badge, UserBadge


async def evaluate_badge_conditions(
    user_id,
    user_total_xp: int,
    db: AsyncSession
) -> List[Badge]:
    """
    Evaluate which badges a user should receive based on their progress.

    Condition types supported:
    - xp: {"type": "xp", "threshold": 1000}
    - attempt_count: {"type": "attempt_count", "count": 10, "status": "passed"}
    - consecutive_days: {"type": "consecutive_days", "days": 7}

    Args:
        user_id: User's UUID
        user_total_xp: User's total XP
        db: Database session

    Returns:
        List of badges the user qualifies for but hasn't received yet
    """
    # Get all badges
    result = await db.execute(select(Badge))
    all_badges = result.scalars().all()

    # Get badges user already has
    result = await db.execute(
        select(UserBadge.badge_id).where(UserBadge.user_id == user_id)
    )
    earned_badge_ids = {row for row in result.scalars().all()}

    badges_to_award = []

    for badge in all_badges:
        # Skip if user already has this badge
        if badge.id in earned_badge_ids:
            continue

        condition = badge.condition
        condition_type = condition.get("type")

        # Evaluate based on condition type
        if condition_type == "xp":
            threshold = condition.get("threshold", 0)
            if user_total_xp >= threshold:
                badges_to_award.append(badge)

        elif condition_type == "attempt_count":
            count_required = condition.get("count", 1)
            status_filter = condition.get("status", "passed")

            # Count attempts matching criteria
            query = select(func.count(Attempt.id)).where(
                Attempt.user_id == user_id,
                Attempt.status == AttemptStatusEnum(status_filter)
            )
            result = await db.execute(query)
            attempt_count = result.scalar()

            if attempt_count >= count_required:
                badges_to_award.append(badge)

        elif condition_type == "consecutive_days":
            days_required = condition.get("days", 7)
            # This is a simplified check - in production, you'd track daily activity
            # For now, we'll check if user has attempts on different days
            query = select(func.date(Attempt.submitted_at)).where(
                Attempt.user_id == user_id,
                Attempt.status == AttemptStatusEnum.PASSED
            ).distinct()
            result = await db.execute(query)
            unique_days = len(result.all())

            if unique_days >= days_required:
                badges_to_award.append(badge)

    return badges_to_award


async def award_badge(
    user_id,
    badge: Badge,
    db: AsyncSession,
    metadata: dict = None
) -> UserBadge:
    """
    Award a badge to a user.

    Args:
        user_id: User's UUID
        badge: Badge to award
        db: Database session
        metadata: Optional metadata about the award

    Returns:
        UserBadge instance
    """
    user_badge = UserBadge(
        user_id=user_id,
        badge_id=badge.id,
        awarded_at=datetime.utcnow(),
        metadata=metadata
    )

    db.add(user_badge)
    await db.commit()
    await db.refresh(user_badge)

    return user_badge
