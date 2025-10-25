"""Dependencies for web routes."""
from typing import Optional
from fastapi import Cookie, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.core.security import decode_token
from app.db.session import async_session_factory
from app.db.models import User
from sqlalchemy import select


async def get_current_user_from_cookie(
    request: Request,
    access_token: Optional[str] = Cookie(None)
) -> Optional[User]:
    """Get current user from cookie token."""
    if not access_token:
        return None

    payload = decode_token(access_token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        return user


async def require_user(
    request: Request,
    access_token: Optional[str] = Cookie(None)
) -> User:
    """Require authenticated user or redirect to login."""
    user = await get_current_user_from_cookie(request, access_token)
    if not user:
        # Redirect to login page
        raise HTTPException(
            status_code=307,
            detail="Authentication required",
            headers={"Location": "/login"}
        )
    return user


def get_optional_user(request: Request):
    """Get user if authenticated, None otherwise (for templates)."""
    return request.state.user if hasattr(request.state, "user") else None
