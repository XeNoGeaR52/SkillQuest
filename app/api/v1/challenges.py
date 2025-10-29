from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.db.models import Challenge, DifficultyEnum, User
from app.db.session import get_db
from app.schemas.challenge import (
    ChallengeCreate,
    ChallengeResponse,
    ChallengeUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[ChallengeResponse])
async def list_challenges(
    difficulty: DifficultyEnum | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List all published challenges with optional filters.

    - **difficulty**: Filter by difficulty level (easy, medium, hard)
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (1-100)
    """
    query = select(Challenge).where(Challenge.published)

    if difficulty:
        query = query.where(Challenge.difficulty == difficulty)

    query = query.offset(skip).limit(limit).order_by(Challenge.created_at.desc())

    result = await db.execute(query)
    challenges = result.scalars().all()

    return challenges


@router.get("/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(
    challenge_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific challenge by ID.
    """
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    challenge = result.scalar_one_or_none()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    return challenge


@router.post("/", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)
async def create_challenge(
    challenge_data: ChallengeCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new challenge (authenticated users only).

    - **title**: Challenge title (3-255 characters)
    - **description**: Challenge description
    - **xp**: XP points awarded (minimum 1)
    - **difficulty**: Difficulty level (easy, medium, hard)
    - **tags**: Optional list of tags
    - **published**: Whether the challenge is published (default: true)
    """
    new_challenge = Challenge(
        title=challenge_data.title,
        description=challenge_data.description,
        xp=challenge_data.xp,
        difficulty=challenge_data.difficulty,
        tags=challenge_data.tags,
        published=challenge_data.published,
        created_by=current_user.id
    )

    db.add(new_challenge)
    await db.commit()
    await db.refresh(new_challenge)

    return new_challenge


@router.put("/{challenge_id}", response_model=ChallengeResponse)
async def update_challenge(
    challenge_id: UUID,
    challenge_data: ChallengeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a challenge (only by creator).

    Only fields provided in the request will be updated.
    """
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    challenge = result.scalar_one_or_none()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    # Check if user is the creator (simple authorization)
    if challenge.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this challenge"
        )

    # Update fields
    update_data = challenge_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(challenge, field, value)

    await db.commit()
    await db.refresh(challenge)

    return challenge


@router.delete("/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_challenge(
    challenge_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a challenge (only by creator).
    """
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    challenge = result.scalar_one_or_none()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    # Check if user is the creator
    if challenge.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this challenge"
        )

    await db.delete(challenge)
    await db.commit()

    return None
