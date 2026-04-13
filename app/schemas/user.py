from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserMeResponse(BaseModel):
    id: str
    name: str
    surname: str
    email: str
    phone_number: str
    role: str
    is_active: bool
    addresses: list["AddressListResponse"] = []


class UpdateMeRequest(BaseModel):
    name: str | None = None
    surname: str | None = None
    phone: str | None = None


class RegisterRequest(BaseModel):
    name: str
    surname: str
    email: str
    phone: str
    password: str
    role: str = "CUSTOMER"


class RegisterResponse(BaseModel):
    id: UUID
    name: str
    surname: str
    email: str
    phone: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ChangePasswordResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ForgotPasswordRequestResponse(BaseModel):
    message: str


class ForgotPasswordConfirmRequest(BaseModel):
    token: str
    new_password: str


class ForgotPasswordConfirmResponse(BaseModel):
    message: str


class AddressLocation(BaseModel):
    lat: float | None = None
    lng: float | None = None


class AddressBase(BaseModel):
    address_title: str
    city: str
    district: str
    neighborhood: str
    street: str
    building_no: str
    floor: str
    apartment_no: str
    address_description: str | None = None
    phone: str
    location: AddressLocation | None = None


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    address_title: str | None = None
    city: str | None = None
    district: str | None = None
    neighborhood: str | None = None
    street: str | None = None
    building_no: str | None = None
    floor: str | None = None
    apartment_no: str | None = None
    address_description: str | None = None
    phone: str | None = None
    location: AddressLocation | None = None


class AddressResponse(BaseModel):
    id: str
    address_title: str
    city: str
    district: str
    neighborhood: str
    street: str
    building_no: str
    floor: str
    apartment_no: str
    address_description: str | None = None
    phone: str
    location: AddressLocation


class AddressListResponse(AddressResponse):
    masked_phone: str
    shows_map_preview: bool
    is_current: bool


class DeleteAddressResponse(BaseModel):
    message: str


class SetCurrentAddressResponse(BaseModel):
    message: str


class FavoriteActionResponse(BaseModel):
    message: str


class FavoriteListItemResponse(BaseModel):
    vendor_id: str
    created_at: datetime


class FavoriteListResponse(BaseModel):
    items: list[FavoriteListItemResponse]
    page: int
    size: int
    total: int


class InternalUserResponse(BaseModel):
    id: UUID
    name: str
    surname: str
    email: str
    phone: str
    role: str
    active: bool


class InternalUserLookupRequest(BaseModel):
    userIds: list[UUID]


class InternalUserLookupItem(BaseModel):
    id: UUID
    name: str
    surname: str
    role: str
    active: bool


class InternalUserLookupResponse(BaseModel):
    users: list[InternalUserLookupItem]


class InternalUserByEmailResponse(BaseModel):
    id: UUID
    email: str
    hashedPassword: str
    role: str
    active: bool


UserMeResponse.model_rebuild()
