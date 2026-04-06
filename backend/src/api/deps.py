"""Dependency injection — DB sessions, auth, rate limiting (Phase 2)."""

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.database import async_session

# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session, auto-closing on exit."""
    async with async_session() as session:
        yield session


# ---------------------------------------------------------------------------
# Auth (simple bearer token — Phase 2 MVP)
# ---------------------------------------------------------------------------

_bearer = HTTPBearer(auto_error=False)

# MVP: accept a static API key. Replace with JWT/OAuth in production.
_VALID_TOKENS = {"resonance-dev-token-2026"}


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Validate bearer token and return operator identity.

    For Phase 2 MVP this checks against a static token set.
    Production will use JWT with expiration.
    """
    if creds is None or creds.credentials not in _VALID_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return "operator"


async def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str | None:
    """Return operator identity if token is valid, None otherwise."""
    if creds is None or creds.credentials not in _VALID_TOKENS:
        return None
    return "operator"
