"""
Operator user CRUD — each route declares the exact RBAC permission it needs.

The super-admin (env-keyed) is never in the ``users`` table, so any response
emitted here is automatically free of the super-admin row.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.application.use_cases import (
    CannotAssignSuperAdmin,
    CreateUser,
    CreateUserInput,
    DeleteUser,
    GetUser,
    ListUsers,
    UpdateUser,
    UpdateUserInput,
    UsernameAlreadyTaken,
    UserNotFound,
)
from src.domain import Permission, Role, User
from src.infrastructure.http.deps import (
    create_user_use_case,
    delete_user_use_case,
    get_user_use_case,
    list_users_use_case,
    update_user_use_case,
)
from src.infrastructure.http.rbac import require_permission

router = APIRouter(prefix="/admin/users", tags=["admin"])


class CreateUserBody(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=200)
    role: Role


class UpdateUserBody(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=100)
    password: str | None = Field(default=None, min_length=8, max_length=200)
    role: Role | None = None


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    created_at: str
    updated_at: str


def _to_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id,
        username=u.username,
        role=u.role.value,
        created_at=u.created_at.isoformat(),
        updated_at=u.updated_at.isoformat(),
    )


@router.get(
    "",
    response_model=list[UserResponse],
    dependencies=[Depends(require_permission(Permission.LIST_USERS))],
)
async def list_users(use_case: ListUsers = Depends(list_users_use_case)) -> list[UserResponse]:
    return [_to_response(u) for u in await use_case.execute()]


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.CREATE_USER))],
)
async def create_user(
    body: CreateUserBody,
    use_case: CreateUser = Depends(create_user_use_case),
) -> UserResponse:
    try:
        user = await use_case.execute(CreateUserInput(username=body.username, password=body.password, role=body.role))
    except CannotAssignSuperAdmin:
        raise HTTPException(status_code=400, detail="cannot assign role super_admin") from None
    except UsernameAlreadyTaken:
        raise HTTPException(status_code=409, detail=f"username already taken: {body.username!r}") from None
    return _to_response(user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permission(Permission.READ_USER))],
)
async def get_user(user_id: str, use_case: GetUser = Depends(get_user_use_case)) -> UserResponse:
    try:
        user = await use_case.execute(user_id)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="user not found") from None
    return _to_response(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permission(Permission.UPDATE_USER))],
)
async def update_user(
    user_id: str,
    body: UpdateUserBody,
    use_case: UpdateUser = Depends(update_user_use_case),
) -> UserResponse:
    try:
        user = await use_case.execute(
            UpdateUserInput(user_id=user_id, username=body.username, password=body.password, role=body.role)
        )
    except CannotAssignSuperAdmin:
        raise HTTPException(status_code=400, detail="cannot assign role super_admin") from None
    except UserNotFound:
        raise HTTPException(status_code=404, detail="user not found") from None
    except UsernameAlreadyTaken:
        raise HTTPException(status_code=409, detail=f"username already taken: {body.username!r}") from None
    return _to_response(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.DELETE_USER))],
)
async def delete_user(user_id: str, use_case: DeleteUser = Depends(delete_user_use_case)) -> None:
    try:
        await use_case.execute(user_id)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="user not found") from None
