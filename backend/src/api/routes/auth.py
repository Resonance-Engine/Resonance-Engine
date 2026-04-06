"""Auth routes — POST /auth/login, GET /auth/me."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# MVP: static credentials. Replace with proper user store in production.
_VALID_CREDENTIALS = {
    "operator": "resonance2026",
    "fairoz": "alpha",
    "reiyyan": "alpha",
    "admin": "admin",
}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    operator: str


@router.post("/login")
async def login(body: LoginRequest) -> LoginResponse:
    """Authenticate operator and return bearer token."""
    expected_pw = _VALID_CREDENTIALS.get(body.username.lower())
    if expected_pw is None or expected_pw != body.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return LoginResponse(
        token="resonance-dev-token-2026",
        operator=body.username.lower(),
    )


@router.get("/me")
async def get_me(user: str = Depends(get_current_user)) -> dict:
    """Return current authenticated operator info."""
    return {"operator": user, "role": "analyst"}
