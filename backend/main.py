"""FastAPI main application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import counselors, interactions, metrics, timeline, agents, weekly_logs, activity_chat, phase_transition
from config import get_settings, setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    setup_logging()
    logger.info("Starting TargetAI Launch Backend")
    yield
    # Shutdown
    logger.info("Shutting down TargetAI Launch Backend")


# Create FastAPI app
app = FastAPI(
    title="TargetAI Launch Management API",
    description="Backend API for TargetAI launch management application",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(counselors.router, prefix="/api/counselors", tags=["counselors"])
app.include_router(interactions.router, prefix="/api/interactions", tags=["interactions"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["timeline"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(weekly_logs.router, prefix="/api/weekly-logs", tags=["weekly-logs"])
app.include_router(activity_chat.router, prefix="/api/chat/activity", tags=["activity-chat"])
app.include_router(phase_transition.router, prefix="/api/phase-transition", tags=["phase-transition"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "TargetAI Launch Management API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
