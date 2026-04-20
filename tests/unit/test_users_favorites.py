import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

try:
    from app.routers import users as users_router
except ModuleNotFoundError:
    users_router = None


class _ScalarList:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _ExecResult:
    def __init__(self, scalar_one=None, scalar_list=None):
        self._scalar_one = scalar_one
        self._scalar_list = scalar_list

    def scalar_one(self):
        return self._scalar_one

    def scalar_one_or_none(self):
        return self._scalar_one

    def scalars(self):
        return _ScalarList(self._scalar_list or [])


class _FakeDb:
    def __init__(self, results):
        self._results = results
        self.calls = 0
        self.added = []
        self.deleted = []
        self.commits = 0

    async def execute(self, _statement):
        result = self._results[self.calls]
        self.calls += 1
        return result

    def add(self, item):
        self.added.append(item)

    async def delete(self, item):
        self.deleted.append(item)

    async def commit(self):
        self.commits += 1


@unittest.skipIf(users_router is None, "fastapi and app dependencies are not installed")
class ListFavoritesTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._original_get_current_user = users_router.get_current_user

        async def _fake_get_current_user(user_id, db):  # pragma: no cover - trivial stub
            return SimpleNamespace(id=user_id)

        users_router.get_current_user = _fake_get_current_user

    async def asyncTearDown(self):
        users_router.get_current_user = self._original_get_current_user

    async def test_list_favorites_returns_paginated_items(self):
        now = datetime(2026, 4, 13, 12, 0, tzinfo=timezone.utc)
        fake_db = _FakeDb(
            [
                _ExecResult(scalar_one=2),
                _ExecResult(
                    scalar_list=[
                        SimpleNamespace(vendor_id="vendor_1", created_at=now),
                        SimpleNamespace(vendor_id="vendor_2", created_at=now),
                    ]
                ),
            ]
        )
        user_id = uuid4()

        response = await users_router.list_favorites(
            page=1,
            size=20,
            user_id=user_id,
            db=fake_db,
        )

        self.assertEqual(fake_db.calls, 2)
        self.assertEqual(response.page, 1)
        self.assertEqual(response.size, 20)
        self.assertEqual(response.total, 2)
        self.assertEqual(len(response.items), 2)
        self.assertEqual(response.items[0].vendor_id, "vendor_1")
        self.assertEqual(response.items[1].vendor_id, "vendor_2")

    async def test_list_favorites_returns_empty_items(self):
        fake_db = _FakeDb(
            [
                _ExecResult(scalar_one=0),
                _ExecResult(scalar_list=[]),
            ]
        )

        response = await users_router.list_favorites(
            page=3,
            size=10,
            user_id=uuid4(),
            db=fake_db,
        )

        self.assertEqual(response.page, 3)
        self.assertEqual(response.size, 10)
        self.assertEqual(response.total, 0)
        self.assertEqual(response.items, [])


@unittest.skipIf(users_router is None, "fastapi and app dependencies are not installed")
class FavoriteMutationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._original_get_current_user = users_router.get_current_user

        async def _fake_get_current_user(user_id, db):  # pragma: no cover - trivial stub
            return SimpleNamespace(id=user_id)

        users_router.get_current_user = _fake_get_current_user

    async def asyncTearDown(self):
        users_router.get_current_user = self._original_get_current_user

    async def test_add_favorite_inserts_and_commits_when_missing(self):
        fake_db = _FakeDb([_ExecResult(scalar_one=None)])

        response = await users_router.add_favorite(
            vendor_id="vendor_101",
            user_id=uuid4(),
            db=fake_db,
        )

        self.assertEqual(response.message, "Vendor added to favorites")
        self.assertEqual(fake_db.calls, 1)
        self.assertEqual(len(fake_db.added), 1)
        self.assertEqual(fake_db.commits, 1)
        self.assertEqual(fake_db.added[0].vendor_id, "vendor_101")

    async def test_add_favorite_is_idempotent_when_already_exists(self):
        existing_favorite = SimpleNamespace(vendor_id="vendor_101")
        fake_db = _FakeDb([_ExecResult(scalar_one=existing_favorite)])

        response = await users_router.add_favorite(
            vendor_id="vendor_101",
            user_id=uuid4(),
            db=fake_db,
        )

        self.assertEqual(response.message, "Vendor added to favorites")
        self.assertEqual(fake_db.calls, 1)
        self.assertEqual(fake_db.added, [])
        self.assertEqual(fake_db.commits, 0)

    async def test_add_favorite_rejects_empty_vendor_id(self):
        fake_db = _FakeDb([])

        with self.assertRaises(Exception) as context:
            await users_router.add_favorite(
                vendor_id="   ",
                user_id=uuid4(),
                db=fake_db,
            )

        self.assertEqual(getattr(context.exception, "status_code", None), 400)
        self.assertEqual(getattr(context.exception, "detail", None), "Invalid vendor_id")
        self.assertEqual(fake_db.calls, 0)

    async def test_remove_favorite_deletes_and_commits_when_exists(self):
        existing_favorite = SimpleNamespace(vendor_id="vendor_101")
        fake_db = _FakeDb([_ExecResult(scalar_one=existing_favorite)])

        response = await users_router.remove_favorite(
            vendor_id="vendor_101",
            user_id=uuid4(),
            db=fake_db,
        )

        self.assertEqual(response.message, "Vendor removed from favorites")
        self.assertEqual(fake_db.calls, 1)
        self.assertEqual(fake_db.deleted, [existing_favorite])
        self.assertEqual(fake_db.commits, 1)

    async def test_remove_favorite_is_idempotent_when_missing(self):
        fake_db = _FakeDb([_ExecResult(scalar_one=None)])

        response = await users_router.remove_favorite(
            vendor_id="vendor_101",
            user_id=uuid4(),
            db=fake_db,
        )

        self.assertEqual(response.message, "Vendor removed from favorites")
        self.assertEqual(fake_db.calls, 1)
        self.assertEqual(fake_db.deleted, [])
        self.assertEqual(fake_db.commits, 0)

    async def test_remove_favorite_rejects_empty_vendor_id(self):
        fake_db = _FakeDb([])

        with self.assertRaises(Exception) as context:
            await users_router.remove_favorite(
                vendor_id="   ",
                user_id=uuid4(),
                db=fake_db,
            )

        self.assertEqual(getattr(context.exception, "status_code", None), 400)
        self.assertEqual(getattr(context.exception, "detail", None), "Invalid vendor_id")
        self.assertEqual(fake_db.calls, 0)


if __name__ == "__main__":
    unittest.main()
