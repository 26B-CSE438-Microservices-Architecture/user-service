from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserMeResponse(BaseModel):
    class NotificationPreferences(BaseModel):
        push_enabled: bool
        sms_enabled: bool
        email_enabled: bool

    id: str
    name: str
    surname: str
    email: str
    phone_number: str
    notification_preferences: NotificationPreferences


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
