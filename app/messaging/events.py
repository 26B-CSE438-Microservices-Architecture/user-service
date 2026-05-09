from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


@dataclass
class UserRegisteredEvent:
    user_id: str
    email: str
    name: str
    surname: str
    role: str
    event_type: str = "user.registered"
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class UserUpdatedEvent:
    user_id: str
    name: str
    surname: str
    phone: str
    event_type: str = "user.updated"
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class UserPasswordChangedEvent:
    user_id: str
    event_type: str = "user.password_changed"
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AddressCreatedEvent:
    user_id: str
    address_id: str
    city: str
    district: str
    event_type: str = "user.address.created"
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AddressUpdatedEvent:
    user_id: str
    address_id: str
    event_type: str = "user.address.updated"
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AddressDeletedEvent:
    user_id: str
    address_id: str
    event_type: str = "user.address.deleted"
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class FavoriteAddedEvent:
    user_id: str
    vendor_id: str
    event_type: str = "user.favorite.added"
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class FavoriteRemovedEvent:
    user_id: str
    vendor_id: str
    event_type: str = "user.favorite.removed"
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class SendEmailCommand:
    to_email: str
    subject: str
    body: str
    command_type: str = "email.send"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
