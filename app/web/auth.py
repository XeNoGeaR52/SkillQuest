"""Authentication routes for web frontend."""
from fastapi import APIRouter, Request, Form, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from app.db.session import async_session_factory
from app.db.models import User
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from datetime import timedelta

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page."""
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Handle login form submission."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Invalid username or password"
                },
                status_code=400
            )

        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Redirect to dashboard with cookies
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=1800,  # 30 minutes
            samesite="lax"
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            max_age=604800,  # 7 days
            samesite="lax"
        )
        return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render registration page."""
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...)
):
    """Handle registration form submission."""
    # Validate passwords match
    if password != password_confirm:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": "Passwords do not match"
            },
            status_code=400
        )

    async with async_session_factory() as session:
        # Check if username exists
        result = await session.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none():
            return templates.TemplateResponse(
                "auth/register.html",
                {
                    "request": request,
                    "error": "Username already exists"
                },
                status_code=400
            )

        # Check if email exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        if result.scalar_one_or_none():
            return templates.TemplateResponse(
                "auth/register.html",
                {
                    "request": request,
                    "error": "Email already exists"
                },
                status_code=400
            )

        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            total_xp=0,
            level=1,
            profile={}
        )
        session.add(user)
        await session.commit()

        # Auto-login after registration
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=1800,
            samesite="lax"
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            max_age=604800,
            samesite="lax"
        )
        return response


@router.post("/logout")
async def logout():
    """Handle logout."""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response
