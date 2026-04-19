import unittest
from unittest.mock import AsyncMock

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from _test_helpers import FakeDb, _ExecResult, make_user, users_router, SKIP_REASON

try:
    from app.schemas.user import UpdateMeRequest
except ModuleNotFoundError:
    UpdateMeRequest = None

_SKIP = unittest.skipIf(users_router is None, SKIP_REASON or "")


@_SKIP
class GetMeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._orig_get_user = users_router.get_current_user
        self._orig_get_addresses = users_router.get_user_addresses

    async def asyncTearDown(self):
        users_router.get_current_user = self._orig_get_user
        users_router.get_user_addresses = self._orig_get_addresses

    async def test_returns_user_profile_with_empty_addresses(self):
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)
        users_router.get_user_addresses = AsyncMock(return_value=[])

        response = await users_router.get_me(user_id=user.id, db=FakeDb([]))

        self.assertEqual(response.email, user.email)
        self.assertEqual(response.name, user.name)
        self.assertEqual(response.addresses, [])


@_SKIP
class UpdateMeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._orig_get_user = users_router.get_current_user
        self._orig_get_addresses = users_router.get_user_addresses

    async def asyncTearDown(self):
        users_router.get_current_user = self._orig_get_user
        users_router.get_user_addresses = self._orig_get_addresses

    async def test_successful_name_update(self):
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)
        users_router.get_user_addresses = AsyncMock(return_value=[])
        fake_db = FakeDb([])

        await users_router.update_me(
            payload=UpdateMeRequest(name="Mehmet"),
            user_id=user.id,
            db=fake_db,
        )

        self.assertEqual(user.name, "Mehmet")
        self.assertEqual(fake_db.commits, 1)

    async def test_no_fields_raises_400(self):
        from fastapi import HTTPException
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)

        with self.assertRaises(HTTPException) as ctx:
            await users_router.update_me(
                payload=UpdateMeRequest(),
                user_id=user.id,
                db=FakeDb([]),
            )

        self.assertEqual(ctx.exception.status_code, 400)

    async def test_phone_conflict_raises_409(self):
        from fastapi import HTTPException
        user = make_user(phone="5551111111")
        other_user = make_user(phone="5559999999")
        users_router.get_current_user = AsyncMock(return_value=user)
        fake_db = FakeDb([_ExecResult(scalar=other_user)])

        with self.assertRaises(HTTPException) as ctx:
            await users_router.update_me(
                payload=UpdateMeRequest(phone="5559999999"),
                user_id=user.id,
                db=fake_db,
            )

        self.assertEqual(ctx.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
