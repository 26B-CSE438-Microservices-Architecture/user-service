from uuid import UUID

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, Path, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.address import Address
from app.models.user import User, UserRole
from app.schemas.user import (
    AddressCreate,
    AddressListResponse,
    AddressLocation,
    AddressResponse,
    AddressUpdate,
    DeleteAddressResponse,
    RegisterRequest,
    RegisterResponse,
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

    hashed_password = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )

    user = User(
        name=f"{normalized_name} {normalized_surname}".strip(),
        email=normalized_email,
        phone=normalized_phone,
        hashed_password=hashed_password,
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return RegisterResponse(
        id=user.id,
        name=normalized_name,
        surname=normalized_surname,
        email=user.email,
        phone=user.phone,
        role=user.role.value,
        created_at=user.created_at,
    )


@router.get("/me", response_model=UserMeResponse)
async def get_me(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(user_id=user_id, db=db)

    name_parts = user.name.strip().split()
    first_name = name_parts[0] if name_parts else ""
    surname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    return UserMeResponse(
        id=f"user_{user.id}",
        name=first_name,
        surname=surname,
        email=user.email,
        phone_number=user.phone,
        notification_preferences=UserMeResponse.NotificationPreferences(
            push_enabled=True,
            sms_enabled=False,
            email_enabled=True,
        ),
    )


@router.get("/me/addresses", response_model=list[AddressListResponse])
async def list_addresses(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user(user_id=user_id, db=db)
    result = await db.execute(select(Address).where(Address.user_id == user_id))
    addresses = result.scalars().all()
    return [to_address_list_response(address) for address in addresses]


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
        select(Address).where(Address.id == parsed_address_id, Address.user_id == user_id)
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
        select(Address).where(Address.id == parsed_address_id, Address.user_id == user_id)
    )
    address = result.scalar_one_or_none()
    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    await db.delete(address)
    await db.commit()
    return DeleteAddressResponse(message="Address deleted")
