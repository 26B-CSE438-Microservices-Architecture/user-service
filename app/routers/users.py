import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.email_utils import enqueue_password_reset_email
from app.messaging.events import (
    AddressCreatedEvent,
    AddressDeletedEvent,
    AddressUpdatedEvent,
    FavoriteAddedEvent,
    FavoriteRemovedEvent,
    UserPasswordChangedEvent,
    UserRegisteredEvent,
    UserUpdatedEvent,
)
from app.messaging.publisher import publish_user_event
from app.models.address import Address
from app.models.favorite import UserFavorite
from app.models.password_reset import PasswordResetToken
from app.models.user import User, UserRole
from app.schemas.user import (
    AddressCreate,
    AddressListResponse,
    AddressLocation,
    AddressResponse,
    AddressUpdate,
    ChangePasswordRequest,
    ChangePasswordResponse,
    DeleteAddressResponse,
    FavoriteActionResponse,
    FavoriteListItemResponse,
    FavoriteListResponse,
    ForgotPasswordConfirmRequest,
    ForgotPasswordConfirmResponse,
    ForgotPasswordRequest,
    ForgotPasswordRequestResponse,
    RegisterRequest,
    RegisterResponse,
    SetCurrentAddressResponse,
    UpdateMeRequest,
    UserMeResponse,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def get_current_user_id(x_user_id: str = Header(..., alias="X-User-Id")) -> UUID:
    try:
        return UUID(x_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-User-Id header",
        ) from exc


async def get_current_user(user_id: UUID, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def mask_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 5:
        return phone
    return f"{digits[:3]}{'*' * max(1, len(digits) - 5)}{digits[-2:]}"


def format_address_id(address_id: UUID) -> str:
    return f"addr_{address_id}"


def parse_address_id(address_id: str) -> UUID:
    raw = address_id[5:] if address_id.startswith("addr_") else address_id
    try:
        return UUID(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid address id",
        ) from exc


def to_address_response(address: Address) -> AddressResponse:
    return AddressResponse(
        id=format_address_id(address.id),
        address_title=address.address_title,
        city=address.city,
        district=address.district,
        neighborhood=address.neighborhood,
        street=address.street,
        building_no=address.building_no,
        floor=address.floor,
        apartment_no=address.apartment_no,
        address_description=address.address_description,
        phone=address.phone,
        location=AddressLocation(lat=address.lat, lng=address.lng),
    )


def to_address_list_response(address: Address) -> AddressListResponse:
    return AddressListResponse(
        **to_address_response(address).model_dump(),
        masked_phone=mask_phone(address.phone),
        shows_map_preview=address.lat is not None and address.lng is not None,
        is_current=address.is_current,
    )


async def get_user_addresses(user_id: UUID, db: AsyncSession) -> list[AddressListResponse]:
    result = await db.execute(
        select(Address).where(Address.user_id == user_id, Address.deleted_at.is_(None))
    )
    addresses = result.scalars().all()
    return [to_address_list_response(address) for address in addresses]


def to_me_response(user: User, addresses: list[AddressListResponse]) -> UserMeResponse:
    return UserMeResponse(
        id=f"user_{user.id}",
        name=user.name,
        surname=user.surname,
        email=user.email,
        phone_number=user.phone,
        role=user.role.value,
        is_active=user.is_active,
        addresses=addresses,
    )


def hash_password(raw_password: str) -> str:
    return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_reset_link(token: str) -> str:
    query_string = urlencode({"token": token})
    return f"{settings.RESET_PASSWORD_URL_BASE}?{query_string}"


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    normalized_name = payload.name.strip()
    normalized_surname = payload.surname.strip()
    normalized_email = payload.email.strip().lower()
    normalized_phone = payload.phone.strip()

    existing = await db.execute(
        select(User).where(
            or_(
                User.email == normalized_email,
                User.phone == normalized_phone,
            )
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or phone already exists",
        )

    try:
        role = UserRole(payload.role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role",
        ) from exc

    hashed_password = hash_password(payload.password)

    user = User(
        name=normalized_name,
        surname=normalized_surname,
        email=normalized_email,
        phone=normalized_phone,
        hashed_password=hashed_password,
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await publish_user_event(
        UserRegisteredEvent(
            user_id=str(user.id),
            email=user.email,
            name=user.name,
            surname=user.surname,
            role=user.role.value,
        ),
        routing_key="user.registered",
    )

    return RegisterResponse(
        id=user.id,
        name=normalized_name,
        surname=normalized_surname,
        email=user.email,
        phone=user.phone,
        role=user.role.value,
        created_at=user.created_at,
    )


@router.post("/me/change-password", response_model=ChangePasswordResponse)
async def change_password(
    payload: ChangePasswordRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(user_id=user_id, db=db)

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    if not bcrypt.checkpw(
        payload.current_password.encode("utf-8"),
        user.hashed_password.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    user.hashed_password = hash_password(payload.new_password)
    await db.commit()

    await publish_user_event(
        UserPasswordChangedEvent(user_id=str(user_id)),
        routing_key="user.password_changed",
    )

    return ChangePasswordResponse(message="Password changed successfully")


@router.post("/forgot-password/request", response_model=ForgotPasswordRequestResponse)
async def request_forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    normalized_email = payload.email.strip().lower()

    result = await db.execute(
        select(User).where(
            User.email == normalized_email,
            User.is_active.is_(True),
        )
    )
    user = result.scalar_one_or_none()

    if user is not None:
        raw_token = secrets.token_urlsafe(32)
        token_record = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_reset_token(raw_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.RESET_PASSWORD_TOKEN_TTL_MINUTES),
        )
        db.add(token_record)
        await db.commit()

        reset_link = build_reset_link(raw_token)
        await enqueue_password_reset_email(user.email, reset_link)

    return ForgotPasswordRequestResponse(
        message="If the email exists, a reset link has been sent"
    )


@router.post("/forgot-password/confirm", response_model=ForgotPasswordConfirmResponse)
async def confirm_forgot_password(
    payload: ForgotPasswordConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    token_hash = hash_reset_token(payload.token.strip())

    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
    )
    token_record = result.scalar_one_or_none()
    if token_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )

    user_result = await db.execute(
        select(User).where(
            User.id == token_record.user_id,
            User.is_active.is_(True),
        )
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if bcrypt.checkpw(
        payload.new_password.encode("utf-8"),
        user.hashed_password.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    user.hashed_password = hash_password(payload.new_password)
    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    token_record.used_at = now
    await db.commit()

    await publish_user_event(
        UserPasswordChangedEvent(user_id=str(user.id)),
        routing_key="user.password_changed",
    )

    return ForgotPasswordConfirmResponse(message="Password reset successfully")


@router.get("/me", response_model=UserMeResponse)
async def get_me(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(user_id=user_id, db=db)
    addresses = await get_user_addresses(user_id=user_id, db=db)
    return to_me_response(user, addresses)


@router.put("/me", response_model=UserMeResponse)
async def update_me(
    payload: UpdateMeRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(user_id=user_id, db=db)

    if payload.name is None and payload.surname is None and payload.phone is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field (name, surname, or phone) must be provided",
        )

    if payload.name is not None:
        user.name = payload.name.strip()
    if payload.surname is not None:
        user.surname = payload.surname.strip()

    if payload.phone is not None:
        normalized_phone = payload.phone.strip()
        if normalized_phone != user.phone:
            existing = await db.execute(
                select(User).where(User.phone == normalized_phone, User.id != user.id)
            )
            if existing.scalar_one_or_none() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Phone already exists",
                )
            user.phone = normalized_phone

    await db.commit()
    await db.refresh(user)

    await publish_user_event(
        UserUpdatedEvent(
            user_id=str(user_id),
            name=user.name,
            surname=user.surname,
            phone=user.phone,
        ),
        routing_key="user.updated",
    )

    addresses = await get_user_addresses(user_id=user_id, db=db)
    return to_me_response(user, addresses)


@router.get("/me/addresses", response_model=list[AddressListResponse])
async def list_addresses(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user(user_id=user_id, db=db)
    return await get_user_addresses(user_id=user_id, db=db)


@router.post("/me/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    payload: AddressCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user(user_id=user_id, db=db)
    address = Address(
        user_id=user_id,
        address_title=payload.address_title,
        city=payload.city,
        district=payload.district,
        neighborhood=payload.neighborhood,
        street=payload.street,
        building_no=payload.building_no,
        floor=payload.floor,
        apartment_no=payload.apartment_no,
        address_description=payload.address_description,
        phone=payload.phone,
        lat=payload.location.lat if payload.location else None,
        lng=payload.location.lng if payload.location else None,
    )
    db.add(address)
    await db.commit()
    await db.refresh(address)

    await publish_user_event(
        AddressCreatedEvent(
            user_id=str(user_id),
            address_id=str(address.id),
            city=address.city,
            district=address.district,
        ),
        routing_key="user.address.created",
    )

    return to_address_response(address)


@router.put("/me/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    payload: AddressUpdate,
    address_id: str = Path(..., description="Address ID"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user(user_id=user_id, db=db)
    parsed_address_id = parse_address_id(address_id)
    result = await db.execute(
        select(Address).where(
            Address.id == parsed_address_id,
            Address.user_id == user_id,
            Address.deleted_at.is_(None),
        )
    )
    address = result.scalar_one_or_none()
    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    location = update_data.pop("location", None)
    for field, value in update_data.items():
        setattr(address, field, value)
    if location is not None:
        address.lat = location["lat"]
        address.lng = location["lng"]

    await db.commit()
    await db.refresh(address)

    await publish_user_event(
        AddressUpdatedEvent(user_id=str(user_id), address_id=str(parsed_address_id)),
        routing_key="user.address.updated",
    )

    return to_address_response(address)


@router.delete("/me/addresses/{address_id}", response_model=DeleteAddressResponse)
async def delete_address(
    address_id: str = Path(..., description="Address ID"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user(user_id=user_id, db=db)
    parsed_address_id = parse_address_id(address_id)
    result = await db.execute(
        select(Address).where(
            Address.id == parsed_address_id,
            Address.user_id == user_id,
            Address.deleted_at.is_(None),
        )
    )
    address = result.scalar_one_or_none()
    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    address.deleted_at = datetime.now(timezone.utc)
    address.is_current = False
    await db.commit()

    await publish_user_event(
        AddressDeletedEvent(user_id=str(user_id), address_id=str(parsed_address_id)),
        routing_key="user.address.deleted",
    )

    return DeleteAddressResponse(message="Address deleted")


@router.patch("/me/addresses/{address_id}/current", response_model=SetCurrentAddressResponse)
async def set_current_address(
    address_id: str = Path(..., description="Address ID"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user(user_id=user_id, db=db)
    parsed_address_id = parse_address_id(address_id)

    result = await db.execute(
        select(Address).where(
            Address.id == parsed_address_id,
            Address.user_id == user_id,
            Address.deleted_at.is_(None),
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    await db.execute(
        update(Address)
        .where(Address.user_id == user_id, Address.deleted_at.is_(None))
        .values(is_current=False)
    )
    target.is_current = True
    await db.commit()

    return SetCurrentAddressResponse(message="Current address updated")


@router.get("/me/favorites", response_model=FavoriteListResponse)
async def list_favorites(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user(user_id=user_id, db=db)

    total_result = await db.execute(
        select(func.count()).select_from(UserFavorite).where(UserFavorite.user_id == user_id)
    )
    total = total_result.scalar_one()

    offset = (page - 1) * size
    result = await db.execute(
        select(UserFavorite)
        .where(UserFavorite.user_id == user_id)
        .order_by(UserFavorite.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    favorites = result.scalars().all()

    return FavoriteListResponse(
        items=[
            FavoriteListItemResponse(vendor_id=item.vendor_id, created_at=item.created_at)
            for item in favorites
        ],
        page=page,
        size=size,
        total=total,
    )


@router.post("/me/favorites/{vendor_id}", response_model=FavoriteActionResponse)
async def add_favorite(
    vendor_id: str = Path(..., description="Vendor ID"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user(user_id=user_id, db=db)
    normalized_vendor_id = vendor_id.strip()
    if not normalized_vendor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vendor_id",
        )

    result = await db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == user_id,
            UserFavorite.vendor_id == normalized_vendor_id,
        )
    )
    favorite = result.scalar_one_or_none()
    if favorite is None:
        db.add(UserFavorite(user_id=user_id, vendor_id=normalized_vendor_id))
        await db.commit()

        await publish_user_event(
            FavoriteAddedEvent(user_id=str(user_id), vendor_id=normalized_vendor_id),
            routing_key="user.favorite.added",
        )

    return FavoriteActionResponse(message="Vendor added to favorites")


@router.delete("/me/favorites/{vendor_id}", response_model=FavoriteActionResponse)
async def remove_favorite(
    vendor_id: str = Path(..., description="Vendor ID"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user(user_id=user_id, db=db)
    normalized_vendor_id = vendor_id.strip()
    if not normalized_vendor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vendor_id",
        )

    result = await db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == user_id,
            UserFavorite.vendor_id == normalized_vendor_id,
        )
    )
    favorite = result.scalar_one_or_none()
    if favorite is not None:
        await db.delete(favorite)
        await db.commit()

        await publish_user_event(
            FavoriteRemovedEvent(user_id=str(user_id), vendor_id=normalized_vendor_id),
            routing_key="user.favorite.removed",
        )

    return FavoriteActionResponse(message="Vendor removed from favorites")
