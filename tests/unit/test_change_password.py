import unittest
from unittest.mock import AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from ._test_helpers import FakeDb, make_user, users_router, SKIP_REASON

try:
    from app.schemas.user import ChangePasswordRequest
except ModuleNotFoundError:
    ChangePasswordRequest = None

_SKIP = unittest.skipIf(users_router is None, SKIP_REASON or "")


@_SKIP
class ChangePasswordTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._original = users_router.get_current_user

    async def asyncTearDown(self):
        users_router.get_current_user = self._original

    async def test_successful_change(self):
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)

        with patch.object(users_router.bcrypt, "checkpw", return_value=True), \
             patch.object(users_router, "hash_password", return_value="new_hashed"):
            response = await users_router.change_password(
                payload=ChangePasswordRequest(current_password="old", new_password="new"),
                user_id=user.id,
                db=FakeDb([]),
            )

        self.assertEqual(response.message, "Password changed successfully")
        self.assertEqual(user.hashed_password, "new_hashed")

    async def test_same_password_raises_400(self):
        from fastapi import HTTPException
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)

        with self.assertRaises(HTTPException) as ctx:
            await users_router.change_password(
                payload=ChangePasswordRequest(current_password="same", new_password="same"),
                user_id=user.id,
                db=FakeDb([]),
            )

        self.assertEqual(ctx.exception.status_code, 400)

    async def test_wrong_current_password_raises_400(self):
        from fastapi import HTTPException
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)

        with patch.object(users_router.bcrypt, "checkpw", return_value=False), \
             self.assertRaises(HTTPException) as ctx:
            await users_router.change_password(
                payload=ChangePasswordRequest(current_password="wrong", new_password="new"),
                user_id=user.id,
                db=FakeDb([]),
            )

        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
