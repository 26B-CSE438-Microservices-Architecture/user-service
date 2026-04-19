"""Shared test infrastructure for user-service unit tests."""
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4


class _ScalarList:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _ExecResult:
    def __init__(self, scalar=None, scalar_list=None):
        self._scalar = scalar
        self._scalar_list = scalar_list

    def scalar_one(self):
        return self._scalar

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return _ScalarList(self._scalar_list or [])


class FakeDb:
    def __init__(self, results, refresh_attrs=None):
        self._results = list(results)
        self._refresh_attrs = refresh_attrs or {}
        self.calls = 0
        self.added = []
        self.deleted = []
        self.commits = 0

    async def execute(self, _statement):
        if self.calls >= len(self._results):
            return _ExecResult()
        result = self._results[self.calls]
        self.calls += 1
        return result

    def add(self, item):
        self.added.append(item)

    async def delete(self, item):
        self.deleted.append(item)

    async def commit(self):
        self.commits += 1

    async def refresh(self, item):
        for key, value in self._refresh_attrs.items():
            setattr(item, key, value)


def make_user(**kwargs):
    defaults = dict(
        id=uuid4(),
        name="Ali",
        surname="Yilmaz",
        email="ali@example.com",
        phone="5551234567",
        hashed_password="$2b$12$hashed",
        role=SimpleNamespace(value="CUSTOMER"),
        is_active=True,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_address(**kwargs):
    defaults = dict(
        id=uuid4(),
        user_id=uuid4(),
        address_title="Home",
        city="Istanbul",
        district="Kadikoy",
        neighborhood="Moda",
        street="Main St",
        building_no="5",
        floor="3",
        apartment_no="7",
        address_description=None,
        phone="5551234567",
        lat=None,
        lng=None,
        is_current=False,
        deleted_at=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


try:
    from app.routers import users as users_router
    SKIP_REASON = None
except ModuleNotFoundError:
    users_router = None
    SKIP_REASON = "fastapi and app dependencies are not installed"
