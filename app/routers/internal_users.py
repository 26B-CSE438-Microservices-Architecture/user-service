from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    InternalUserByEmailResponse,
    InternalUserLookupItem,
    InternalUserLookupRequest,
    InternalUserLookupResponse,
    InternalUserResponse,
)

router = APIRouter(prefix="/internal/v1/users", tags=["internal-users"])


@router.post("/lookup", response_model=InternalUserLookupResponse)
async def lookup_users(
    payload: InternalUserLookupRequest,
    db: AsyncSession = Depends(get_db),
):
    if not payload.userIds:
        return InternalUserLookupResponse(users=[])

    result = await db.execute(select(User).where(User.id.in_(payload.userIds)))
    users = result.scalars().all()

    return InternalUserLookupResponse(
        users=[
            InternalUserLookupItem(
                id=user.id,
                name=user.name,
                surname=user.surname,
                role=user.role.value,
                active=user.is_active,
            )
            for user in users
        ]
    )


@router.get("/by-email", response_model=InternalUserByEmailResponse)
async def get_user_by_email(
    email: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    normalized_email = email.strip().lower()
    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return InternalUserByEmailResponse(
        id=user.id,
        email=user.email,
        hashedPassword=user.hashed_password,
        role=user.role.value,
        active=user.is_active,
    )


@router.get("/{user_id}", response_model=InternalUserResponse)
async def get_user_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return InternalUserResponse(
        id=user.id,
        name=user.name,
        surname=user.surname,
        email=user.email,
        phone=user.phone,
        role=user.role.value,
        active=user.is_active,
    )
