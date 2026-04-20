import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from ._test_helpers import FakeDb, _ExecResult, make_user, users_router, SKIP_REASON

try:
    from app.schemas.user import ForgotPasswordConfirmRequest, ForgotPasswordRequest
except ModuleNotFoundError:
    ForgotPasswordRequest = None
    ForgotPasswordConfirmRequest = None

_SKIP = unittest.skipIf(users_router is None, SKIP_REASON or "")


@_SKIP
class ForgotPasswordRequestTests(unittest.IsolatedAsyncioTestCase):
    async def test_user_exists_creates_token_and_sends_email(self):
        user = make_user()
        fake_db = FakeDb([_ExecResult(scalar=user)])

        with patch.object(users_router, "build_reset_link", return_value="http://reset?token=abc"), \
             patch("app.routers.users.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            response = await users_router.request_forgot_password(
                payload=ForgotPasswordRequest(email="ali@example.com"),
                db=fake_db,
            )

        self.assertEqual(response.message, "If the email exists, a reset link has been sent")
        self.assertEqual(fake_db.commits, 1)
        self.assertEqual(len(fake_db.added), 1)
        mock_thread.assert_called_once()

    async def test_user_not_found_returns_same_message(self):
        fake_db = FakeDb([_ExecResult(scalar=None)])

        response = await users_router.request_forgot_password(
            payload=ForgotPasswordRequest(email="notfound@example.com"),
            db=fake_db,
        )

        self.assertEqual(response.message, "If the email exists, a reset link has been sent")
        self.assertEqual(fake_db.commits, 0)
        self.assertEqual(fake_db.added, [])

    async def test_email_send_failure_raises_503(self):
        from fastapi import HTTPException
        user = make_user()
        fake_db = FakeDb([_ExecResult(scalar=user)])

        with patch.object(users_router, "build_reset_link", return_value="http://reset?token=abc"), \
             patch("app.routers.users.asyncio.to_thread", AsyncMock(side_effect=RuntimeError("SMTP"))), \
             self.assertRaises(HTTPException) as ctx:
            await users_router.request_forgot_password(
                payload=ForgotPasswordRequest(email="ali@example.com"),
                db=fake_db,
            )

        self.assertEqual(ctx.exception.status_code, 503)


@_SKIP
class ForgotPasswordConfirmTests(unittest.IsolatedAsyncioTestCase):
    def _make_token_record(self, user_id):
        return SimpleNamespace(
            user_id=user_id,
            token_hash="hash",
            used_at=None,
            expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
        )

    async def test_invalid_token_raises_400(self):
        from fastapi import HTTPException
        fake_db = FakeDb([_ExecResult(scalar=None)])

        with self.assertRaises(HTTPException) as ctx:
            await users_router.confirm_forgot_password(
                payload=ForgotPasswordConfirmRequest(token="bad", new_password="newpass"),
                db=fake_db,
            )

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "Invalid or expired token")

    async def test_user_not_found_raises_404(self):
        from fastapi import HTTPException
        user = make_user()
        token_record = self._make_token_record(user.id)
        fake_db = FakeDb([_ExecResult(scalar=token_record), _ExecResult(scalar=None)])

        with self.assertRaises(HTTPException) as ctx:
            await users_router.confirm_forgot_password(
                payload=ForgotPasswordConfirmRequest(token="validtoken", new_password="newpass"),
                db=fake_db,
            )

        self.assertEqual(ctx.exception.status_code, 404)

    async def test_same_password_raises_400(self):
        from fastapi import HTTPException
        user = make_user()
        token_record = self._make_token_record(user.id)
        fake_db = FakeDb([_ExecResult(scalar=token_record), _ExecResult(scalar=user)])

        with patch.object(users_router.bcrypt, "checkpw", return_value=True), \
             self.assertRaises(HTTPException) as ctx:
            await users_router.confirm_forgot_password(
                payload=ForgotPasswordConfirmRequest(token="validtoken", new_password="samepass"),
                db=fake_db,
            )

        self.assertEqual(ctx.exception.status_code, 400)

    async def test_successful_reset(self):
        user = make_user()
        token_record = self._make_token_record(user.id)
        fake_db = FakeDb([
            _ExecResult(scalar=token_record),
            _ExecResult(scalar=user),
            _ExecResult(),
        ])

        with patch.object(users_router.bcrypt, "checkpw", return_value=False), \
             patch.object(users_router, "hash_password", return_value="new_hashed"):
            response = await users_router.confirm_forgot_password(
                payload=ForgotPasswordConfirmRequest(token="validtoken", new_password="newpass"),
                db=fake_db,
            )

        self.assertEqual(response.message, "Password reset successfully")
        self.assertEqual(user.hashed_password, "new_hashed")
        self.assertEqual(fake_db.commits, 1)


if __name__ == "__main__":
    unittest.main()
