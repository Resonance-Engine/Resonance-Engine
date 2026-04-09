"""FastAPI application factory — REST API for Resonance Engine."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.middleware import setup_middleware
from src.api.routes import auth, entities, events, health, pipeline, signals
from src.gateway.server import router as ws_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle — startup / shutdown."""
    logger.info("Resonance Engine API starting up")

    # Start async EDGAR polling scheduler (replaces Celery Beat)
    from src.scheduler import start_scheduler, stop_scheduler
    await start_scheduler()

    yield

    # Shutdown: stop scheduler, dispose DB engine
    await stop_scheduler()
    from src.storage.database import engine
    await engine.dispose()
    logger.info("Resonance Engine API shut down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Resonance Engine API",
        version="4.0.1",
        description="Financial intelligence platform — signals, events, entities",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Middleware (CORS, logging, error handling)
    setup_middleware(app)

    # Routes
    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(signals.router, prefix="/api")
    app.include_router(events.router, prefix="/api")
    app.include_router(entities.router, prefix="/api")
    app.include_router(pipeline.router, prefix="/api")

    # WebSocket gateway (real-time signal push)
    app.include_router(ws_router, prefix="/api")

    return app


# Uvicorn entry point: `uvicorn src.api.app:app --reload`
app = create_app()
