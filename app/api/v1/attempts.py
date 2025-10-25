from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.db.models import Attempt, Challenge, User, AttemptStatusEnum
from app.schemas.attempt import AttemptCreate, AttemptSubmit, AttemptResponse
from app.core.deps import get_current_active_user

router = APIRouter()


@router.post("/", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED)
async def create_attempt(
    attempt_data: AttemptCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new attempt for a challenge.

    - **challenge_id**: UUID of the challenge to attempt
    """
    # Verify challenge exists
    result = await db.execute(
        select(Challenge).where(Challenge.id == attempt_data.challenge_id)
    )
    challenge = result.scalar_one_or_none()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    if not challenge.published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Challenge is not published"
        )

    # Create new attempt
    new_attempt = Attempt(
        user_id=current_user.id,
        challenge_id=attempt_data.challenge_id,
        status=AttemptStatusEnum.STARTED,
        started_at=datetime.utcnow()
    )

    db.add(new_attempt)
    await db.commit()
    await db.refresh(new_attempt)

    return new_attempt


@router.post("/{attempt_id}/submit", response_model=AttemptResponse)
async def submit_attempt(
    attempt_id: UUID,
    submit_data: AttemptSubmit,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit an attempt with a score.

    This endpoint will:
    1. Update the attempt with the score and status
    2. Enqueue a background job to award XP and check for badges

    - **score**: Score achieved (0-100)
    - **solution**: Optional solution submitted
    - **metadata**: Optional metadata
    """
    # Get the attempt
    result = await db.execute(
        select(Attempt).where(Attempt.id == attempt_id)
    )
    attempt = result.scalar_one_or_none()

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found"
        )

    # Verify user owns this attempt
    if attempt.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to submit this attempt"
        )

    # Check if already submitted
    if attempt.status in [AttemptStatusEnum.SUBMITTED, AttemptStatusEnum.PASSED, AttemptStatusEnum.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempt already submitted"
        )

    # Update attempt
    attempt.score = submit_data.score
    attempt.submitted_at = datetime.utcnow()
    attempt.status = AttemptStatusEnum.SUBMITTED

    # Store solution in metadata
    if submit_data.metadata:
        attempt.attempt_metadata = submit_data.metadata
    else:
        attempt.attempt_metadata = {}

    if submit_data.solution:
        attempt.attempt_metadata["solution"] = submit_data.solution

    await db.commit()
    await db.refresh(attempt)

    # Enqueue background task to process XP and badges
    # Import here to avoid circular dependency
    from app.tasks.worker import award_xp_and_badges
    award_xp_and_badges.delay(str(attempt.id))

    return attempt


@router.get("/", response_model=List[AttemptResponse])
async def list_attempts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List current user's attempts.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (1-100)
    """
    query = select(Attempt).where(
        Attempt.user_id == current_user.id
    ).offset(skip).limit(limit).order_by(Attempt.started_at.desc())

    result = await db.execute(query)
    attempts = result.scalars().all()

    return attempts


@router.get("/{attempt_id}", response_model=AttemptResponse)
async def get_attempt(
    attempt_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific attempt by ID.
    """
    result = await db.execute(
        select(Attempt).where(Attempt.id == attempt_id)
    )
    attempt = result.scalar_one_or_none()

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found"
        )

    # Verify user owns this attempt
    if attempt.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this attempt"
        )

    return attempt
