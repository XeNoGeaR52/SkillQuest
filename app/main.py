from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import attempts, auth, badges, challenges, leaderboard
from app.core.config import settings
from app.web import auth as web_auth
from app.web import routes as web_routes

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="1.0.0",
    description="A gamification platform where users complete challenges to earn XP and badges"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0"
    }


# Include API routers (with /api prefix to distinguish from web routes)
app.include_router(auth.router, prefix="/api/auth", tags=["API Authentication"])
app.include_router(challenges.router, prefix="/api/challenges", tags=["API Challenges"])
app.include_router(attempts.router, prefix="/api/attempts", tags=["API Attempts"])
app.include_router(badges.router, prefix="/api/badges", tags=["API Badges"])
app.include_router(leaderboard.router, prefix="/api", tags=["API Leaderboard"])

# Include web frontend routers (no prefix - these serve HTML)
app.include_router(web_auth.router, tags=["Web Authentication"])
app.include_router(web_routes.router, tags=["Web Pages"])
