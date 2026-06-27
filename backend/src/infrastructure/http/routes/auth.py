"""
Session-based authentication for the admin.

Three endpoints:

- ``POST /auth/login`` — validates credentials, sets the signed session
  cookie carrying ``username`` + ``role``. Returns 200 on success, 401
  otherwise. Doesn't distinguish unknown user / wrong password.
- ``POST /auth/logout`` — clears the session.
- ``GET  /auth/me`` — returns the current ``{username, role}``, or 401
  if no session is active. Used by SvelteKit's auth guard on each SSR load.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.application.ports import UserRepositoryPort
from src.domain import Role
from src.infrastructure.http.credentials import authenticate
from src.infrastructure.http.deps import user_repository

router = APIRouter(prefix="/auth", tags=["auth"])

_SESSION_USER = "admin_username"
_SESSION_ROLE = "admin_role"


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class MeResponse(BaseModel):
    username: str
    role: str


@router.post("/login", response_model=MeResponse)
async def login(
    body: LoginRequest,
    request: Request,
    users: UserRepositoryPort = Depends(user_repository),
) -> MeResponse:
    principal = await authenticate(body.username, body.password, users)
    if principal is None:
        # Same status whether the user exists or the password is wrong, so
        # an attacker can't enumerate accounts.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    request.session[_SESSION_USER] = principal.username
    request.session[_SESSION_ROLE] = principal.role.value
    return MeResponse(username=principal.username, role=principal.role.value)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request) -> None:
    request.session.clear()


@router.get("/me", response_model=MeResponse)
async def me(request: Request) -> MeResponse:
    username = request.session.get(_SESSION_USER)
    role_str = request.session.get(_SESSION_ROLE)
    if not username or not role_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    try:
        Role(role_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="stale session") from None
    return MeResponse(username=username, role=role_str)
