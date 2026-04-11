"""Health check route — GET /health."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Return service health with database connectivity status."""
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        logger.warning("Database health check failed")

    # API quota status
    from src.ingestion.quota import (
        alpha_vantage_quota,
        finnhub_quota,
        gemini_quota,
        newsapi_quota,
    )

    status = "healthy" if db_ok else "degraded"
    return {
        "status": status,
        "service": "resonance-engine",
        "version": "4.0.1",
        "database": "connected" if db_ok else "unavailable",
        "quotas": {
            "newsapi": newsapi_quota.status(),
            "alpha_vantage": alpha_vantage_quota.status(),
            "finnhub": finnhub_quota.status(),
            "gemini": gemini_quota.status(),
        },
    }
