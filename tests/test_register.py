import unittest
from unittest.mock import patch
from uuid import uuid4
from datetime import datetime, timezone

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from _test_helpers import FakeDb, _ExecResult, make_user, users_router, SKIP_REASON

try:
    from app.schemas.user import RegisterRequest
except ModuleNotFoundError:
    RegisterRequest = None

_SKIP = unittest.skipIf(users_router is None, SKIP_REASON or "")


@_SKIP
class RegisterTests(unittest.IsolatedAsyncioTestCase):
    async def test_successful_registration(self):
        user_id = uuid4()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        fake_db = FakeDb(
            [_ExecResult(scalar=None)],
            refresh_attrs={"id": user_id, "created_at": now},
        )
        payload = RegisterRequest(
            name="Ali",
            surname="Yilmaz",
            email="ali@example.com",
            phone="5551234567",
            password="password123",
            role="CUSTOMER",
        )

        with patch.object(users_router, "hash_password", return_value="hashed"):
            response = await users_router.register_user(payload=payload, db=fake_db)

        self.assertEqual(response.email, "ali@example.com")
        self.assertEqual(response.role, "CUSTOMER")
        self.assertEqual(len(fake_db.added), 1)
        self.assertEqual(fake_db.commits, 1)

    async def test_duplicate_email_or_phone_raises_409(self):
        from fastapi import HTTPException
        fake_db = FakeDb([_ExecResult(scalar=make_user())])
        payload = RegisterRequest(
            name="Ali",
            surname="Yilmaz",
            email="ali@example.com",
            phone="5551234567",
            password="password123",
        )

        with self.assertRaises(HTTPException) as ctx:
            await users_router.register_user(payload=payload, db=fake_db)

        self.assertEqual(ctx.exception.status_code, 409)

    async def test_invalid_role_raises_400(self):
        from fastapi import HTTPException
        fake_db = FakeDb([_ExecResult(scalar=None)])
        payload = RegisterRequest(
            name="Ali",
            surname="Yilmaz",
            email="ali@example.com",
            phone="5551234567",
            password="password123",
            role="INVALID_ROLE",
        )

        with patch.object(users_router, "hash_password", return_value="hashed"), \
             self.assertRaises(HTTPException) as ctx:
            await users_router.register_user(payload=payload, db=fake_db)

        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
