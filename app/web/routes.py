"""Main web routes for SkillQuest frontend."""
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from uuid import UUID
import httpx

from app.db.session import async_session_factory
from app.db.models import User, Challenge, Attempt, Badge, UserBadge
from app.web.deps import get_current_user_from_cookie, require_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: Optional[User] = Depends(get_current_user_from_cookie)
):
    """Dashboard page - shows user stats and recent activity."""
    if not user:
        # Redirect to login if not authenticated
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=303)

    async with async_session_factory() as session:
        # Refresh user data
        result = await session.execute(
            select(User).where(User.id == user.id)
        )
        user = result.scalar_one()

        # Get recent attempts
        attempts_result = await session.execute(
            select(Attempt)
            .where(Attempt.user_id == user.id)
            .options(selectinload(Attempt.challenge))
            .order_by(desc(Attempt.started_at))
            .limit(5)
        )
        recent_attempts = attempts_result.scalars().all()

        # Get recent badges
        badges_result = await session.execute(
            select(UserBadge)
            .where(UserBadge.user_id == user.id)
            .options(selectinload(UserBadge.badge))
            .order_by(desc(UserBadge.awarded_at))
            .limit(3)
        )
        recent_badges = badges_result.scalars().all()

        # Get total challenges completed
        completed_count = await session.execute(
            select(func.count(Attempt.id))
            .where(Attempt.user_id == user.id)
            .where(Attempt.status == "passed")
        )
        total_completed = completed_count.scalar()

        # Calculate XP to next level
        current_xp = user.total_xp
        current_level = user.level
        next_level_xp = (current_level ** 2) * 100
        xp_progress = (current_xp - ((current_level - 1) ** 2) * 100) / (next_level_xp - ((current_level - 1) ** 2) * 100) * 100

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": user,
            "recent_attempts": recent_attempts,
            "recent_badges": recent_badges,
            "total_completed": total_completed,
            "next_level_xp": next_level_xp,
            "xp_progress": min(xp_progress, 100)
        })


@router.get("/challenges", response_class=HTMLResponse)
async def challenges_list(
    request: Request,
    difficulty: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    user: Optional[User] = Depends(get_current_user_from_cookie)
):
    """List all challenges with filtering."""
    if not user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=303)

    limit = 12
    skip = (page - 1) * limit

    async with async_session_factory() as session:
        # Build query
        query = select(Challenge).where(Challenge.published == True)

        if difficulty:
            query = query.where(Challenge.difficulty == difficulty)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(desc(Challenge.created_at)).offset(skip).limit(limit)
        result = await session.execute(query)
        challenges = result.scalars().all()

        total_pages = (total + limit - 1) // limit

        return templates.TemplateResponse("challenges/list.html", {
            "request": request,
            "user": user,
            "challenges": challenges,
            "difficulty": difficulty,
            "page": page,
            "total_pages": total_pages
        })


@router.get("/challenges/{challenge_id}", response_class=HTMLResponse)
async def challenge_detail(
    request: Request,
    challenge_id: UUID,
    user: User = Depends(require_user)
):
    """Challenge detail page."""
    async with async_session_factory() as session:
        # Get challenge
        result = await session.execute(
            select(Challenge).where(Challenge.id == challenge_id)
        )
        challenge = result.scalar_one_or_none()

        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")

        # Get user's attempts for this challenge
        attempts_result = await session.execute(
            select(Attempt)
            .where(Attempt.user_id == user.id)
            .where(Attempt.challenge_id == challenge_id)
            .order_by(desc(Attempt.started_at))
        )
        user_attempts = attempts_result.scalars().all()

        return templates.TemplateResponse("challenges/detail.html", {
            "request": request,
            "user": user,
            "challenge": challenge,
            "user_attempts": user_attempts
        })


@router.post("/challenges/{challenge_id}/start")
async def start_challenge(
    challenge_id: UUID,
    user: User = Depends(require_user)
):
    """Start a new attempt (htmx endpoint)."""
    async with async_session_factory() as session:
        # Create new attempt
        attempt = Attempt(
            user_id=user.id,
            challenge_id=challenge_id,
            status="started"
        )
        session.add(attempt)
        await session.commit()
        await session.refresh(attempt)

        # Return success message for htmx
        return HTMLResponse(
            content=f'<div class="alert alert-success">Challenge started! Attempt ID: {attempt.id}</div>',
            status_code=200
        )


@router.post("/attempts/{attempt_id}/submit")
async def submit_attempt(
    request: Request,
    attempt_id: UUID,
    score: int = Form(..., ge=0, le=100),
    solution: Optional[str] = Form(None),
    user: User = Depends(require_user)
):
    """Submit an attempt (htmx endpoint)."""
    async with async_session_factory() as session:
        # Get attempt
        result = await session.execute(
            select(Attempt)
            .where(Attempt.id == attempt_id)
            .where(Attempt.user_id == user.id)
            .options(selectinload(Attempt.challenge))
        )
        attempt = result.scalar_one_or_none()

        if not attempt:
            raise HTTPException(status_code=404, detail="Attempt not found")

        # Update attempt
        attempt.status = "passed" if score >= 70 else "failed"
        attempt.score = score
        attempt.xp_awarded = int(attempt.challenge.xp * (score / 100))
        attempt.attempt_metadata = {"solution": solution} if solution else {}

        from datetime import datetime
        attempt.submitted_at = datetime.utcnow()

        # Update user XP
        user.total_xp += attempt.xp_awarded
        user.level = int((user.total_xp / 100) ** 0.5) + 1

        await session.commit()

        # Return success HTML for htmx
        status_class = "success" if attempt.status == "passed" else "danger"
        return HTMLResponse(
            content=f'''
            <div class="alert alert-{status_class}">
                <strong>{'Passed!' if attempt.status == 'passed' else 'Failed'}</strong><br>
                Score: {score}/100<br>
                XP Awarded: {attempt.xp_awarded}<br>
                <a href="/progress" class="btn btn-sm btn-primary mt-2">View Progress</a>
            </div>
            ''',
            status_code=200
        )


@router.get("/progress", response_class=HTMLResponse)
async def progress_page(
    request: Request,
    user: User = Depends(require_user)
):
    """User progress page."""
    async with async_session_factory() as session:
        # Refresh user
        result = await session.execute(
            select(User).where(User.id == user.id)
        )
        user = result.scalar_one()

        # Get all user badges
        badges_result = await session.execute(
            select(UserBadge)
            .where(UserBadge.user_id == user.id)
            .options(selectinload(UserBadge.badge))
            .order_by(desc(UserBadge.awarded_at))
        )
        earned_badges = badges_result.scalars().all()

        # Get recent attempts
        attempts_result = await session.execute(
            select(Attempt)
            .where(Attempt.user_id == user.id)
            .options(selectinload(Attempt.challenge))
            .order_by(desc(Attempt.started_at))
            .limit(10)
        )
        recent_attempts = attempts_result.scalars().all()

        # Calculate stats
        total_attempts = await session.execute(
            select(func.count(Attempt.id)).where(Attempt.user_id == user.id)
        )
        total_attempts_count = total_attempts.scalar()

        passed_attempts = await session.execute(
            select(func.count(Attempt.id))
            .where(Attempt.user_id == user.id)
            .where(Attempt.status == "passed")
        )
        passed_count = passed_attempts.scalar()

        return templates.TemplateResponse("progress.html", {
            "request": request,
            "user": user,
            "earned_badges": earned_badges,
            "recent_attempts": recent_attempts,
            "total_attempts": total_attempts_count,
            "passed_count": passed_count
        })


@router.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_from_cookie)
):
    """Leaderboard page."""
    async with async_session_factory() as session:
        # Get top users
        result = await session.execute(
            select(User)
            .order_by(desc(User.total_xp))
            .limit(50)
        )
        top_users = result.scalars().all()

        # Get current user's rank if authenticated
        user_rank = None
        if user:
            rank_result = await session.execute(
                select(func.count(User.id))
                .where(User.total_xp > user.total_xp)
            )
            user_rank = rank_result.scalar() + 1

        return templates.TemplateResponse("leaderboard.html", {
            "request": request,
            "user": user,
            "top_users": top_users,
            "user_rank": user_rank
        })


@router.get("/badges", response_class=HTMLResponse)
async def badges_page(
    request: Request,
    user: User = Depends(require_user)
):
    """Badges gallery page."""
    async with async_session_factory() as session:
        # Get all badges
        all_badges_result = await session.execute(select(Badge))
        all_badges = all_badges_result.scalars().all()

        # Get user's earned badges
        earned_result = await session.execute(
            select(UserBadge.badge_id).where(UserBadge.user_id == user.id)
        )
        earned_badge_ids = {row[0] for row in earned_result.all()}

        return templates.TemplateResponse("badges.html", {
            "request": request,
            "user": user,
            "all_badges": all_badges,
            "earned_badge_ids": earned_badge_ids
        })


@router.get("/account", response_class=HTMLResponse)
async def account_page(
    request: Request,
    user: User = Depends(require_user)
):
    """User account settings page."""
    async with async_session_factory() as session:
        # Refresh user data
        result = await session.execute(
            select(User).where(User.id == user.id)
        )
        user = result.scalar_one()

        # Get badge count
        badge_count_result = await session.execute(
            select(func.count(UserBadge.id)).where(UserBadge.user_id == user.id)
        )
        badge_count = badge_count_result.scalar()

        return templates.TemplateResponse("account.html", {
            "request": request,
            "user": user,
            "badge_count": badge_count
        })


@router.post("/account/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    user: User = Depends(require_user)
):
    """Change user password."""
    # Validate passwords match
    if new_password != confirm_password:
        return HTMLResponse(
            content='<div class="alert alert-danger mb-4">New passwords do not match</div>',
            status_code=400
        )

    # Validate password length
    if len(new_password) < 8:
        return HTMLResponse(
            content='<div class="alert alert-danger mb-4">Password must be at least 8 characters</div>',
            status_code=400
        )

    async with async_session_factory() as session:
        # Get fresh user data with password
        result = await session.execute(
            select(User).where(User.id == user.id)
        )
        user = result.scalar_one()

        # Verify current password
        from app.core.security import verify_password, get_password_hash
        if not verify_password(current_password, user.password_hash):
            return HTMLResponse(
                content='<div class="alert alert-danger mb-4">Current password is incorrect</div>',
                status_code=400
            )

        # Update password
        user.password_hash = get_password_hash(new_password)
        await session.commit()

        return HTMLResponse(
            content='<div class="alert alert-success mb-4">Password changed successfully!</div>',
            status_code=200
        )


@router.post("/account/delete")
async def delete_account(
    request: Request,
    user: User = Depends(require_user)
):
    """Delete user account."""
    async with async_session_factory() as session:
        # Get fresh user
        result = await session.execute(
            select(User).where(User.id == user.id)
        )
        user = result.scalar_one()

        # Delete user (cascade will delete related records)
        await session.delete(user)
        await session.commit()

        # Clear cookies and redirect to login
        from fastapi.responses import RedirectResponse
        response = RedirectResponse(url="/login?deleted=true", status_code=303)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response
