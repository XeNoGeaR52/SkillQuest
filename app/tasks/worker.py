from uuid import UUID

import redis
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models import Attempt, AttemptStatusEnum, Challenge, User
from app.services.xp_service import calculate_level, calculate_xp_awarded, is_passing_score

# Create Celery app
celery_app = Celery(
    "skillquest",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Create synchronous database session for Celery tasks
# (Celery doesn't work well with async code, so we use sync SQLAlchemy)
sync_db_url = settings.DATABASE_URL.replace("+asyncpg", "")
sync_engine = create_engine(sync_db_url, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

# Redis client for leaderboard
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


@celery_app.task(name="award_xp_and_badges")
def award_xp_and_badges(attempt_id: str):
    """
    Background task to award XP and badges after an attempt is submitted.

    Args:
        attempt_id: UUID of the attempt (as string)
    """
    db = SyncSessionLocal()

    try:
        # Load attempt with related challenge
        attempt_uuid = UUID(attempt_id)
        attempt = db.query(Attempt).filter(Attempt.id == attempt_uuid).first()

        if not attempt:
            print(f"Attempt {attempt_id} not found")
            return

        # Load challenge
        challenge = db.query(Challenge).filter(Challenge.id == attempt.challenge_id).first()

        if not challenge:
            print(f"Challenge {attempt.challenge_id} not found")
            return

        # Calculate XP awarded
        xp_awarded = calculate_xp_awarded(challenge.xp, attempt.score or 0)
        attempt.xp_awarded = xp_awarded

        # Determine if passing
        passing = is_passing_score(attempt.score or 0)
        attempt.status = AttemptStatusEnum.PASSED if passing else AttemptStatusEnum.FAILED

        # Update user's total XP (atomic operation)
        if passing:
            user = db.query(User).filter(User.id == attempt.user_id).first()
            if user:
                user.total_xp += xp_awarded
                user.level = calculate_level(user.total_xp)

                # Update leaderboard in Redis
                redis_client.zadd("leaderboard", {str(user.id): user.total_xp})

                print(f"Awarded {xp_awarded} XP to user {user.id}. Total XP: {user.total_xp}, Level: {user.level}")

                # Check for badges (synchronously evaluate conditions)
                badges_to_award = evaluate_badge_conditions_sync(user.id, user.total_xp, db)

                for badge in badges_to_award:
                    award_badge_sync(user.id, badge, db)
                    print(f"Awarded badge '{badge.name}' to user {user.id}")

        db.commit()
        print(f"Successfully processed attempt {attempt_id}")

    except Exception as e:
        db.rollback()
        print(f"Error processing attempt {attempt_id}: {str(e)}")
        raise
    finally:
        db.close()


def evaluate_badge_conditions_sync(user_id, user_total_xp: int, db):
    """Synchronous version of badge evaluation for Celery."""
    from sqlalchemy import func

    from app.db.models import Badge, UserBadge

    # Get all badges
    all_badges = db.query(Badge).all()

    # Get badges user already has
    earned_badge_ids = {
        row[0] for row in db.query(UserBadge.badge_id).filter(UserBadge.user_id == user_id).all()
    }

    badges_to_award = []

    for badge in all_badges:
        if badge.id in earned_badge_ids:
            continue

        condition = badge.condition
        condition_type = condition.get("type")

        if condition_type == "xp":
            threshold = condition.get("threshold", 0)
            if user_total_xp >= threshold:
                badges_to_award.append(badge)

        elif condition_type == "attempt_count":
            count_required = condition.get("count", 1)
            status_filter = condition.get("status", "passed")

            attempt_count = db.query(func.count(Attempt.id)).filter(
                Attempt.user_id == user_id,
                Attempt.status == AttemptStatusEnum(status_filter)
            ).scalar()

            if attempt_count >= count_required:
                badges_to_award.append(badge)

        elif condition_type == "consecutive_days":
            days_required = condition.get("days", 7)
            unique_days = db.query(func.date(Attempt.submitted_at)).filter(
                Attempt.user_id == user_id,
                Attempt.status == AttemptStatusEnum.PASSED
            ).distinct().count()

            if unique_days >= days_required:
                badges_to_award.append(badge)

    return badges_to_award


def award_badge_sync(user_id, badge, db):
    """Synchronous version of badge awarding for Celery."""
    from datetime import datetime

    from app.db.models import UserBadge

    user_badge = UserBadge(
        user_id=user_id,
        badge_id=badge.id,
        awarded_at=datetime.utcnow()
    )

    db.add(user_badge)
    db.commit()
