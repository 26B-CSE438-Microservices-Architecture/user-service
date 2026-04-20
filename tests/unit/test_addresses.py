import unittest
from unittest.mock import AsyncMock
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from ._test_helpers import FakeDb, _ExecResult, make_user, make_address, users_router, SKIP_REASON

try:
    from app.schemas.user import AddressCreate, AddressUpdate
except ModuleNotFoundError:
    AddressCreate = None
    AddressUpdate = None

_SKIP = unittest.skipIf(users_router is None, SKIP_REASON or "")


@_SKIP
class AddressTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._orig_get_user = users_router.get_current_user

    async def asyncTearDown(self):
        users_router.get_current_user = self._orig_get_user

    async def test_list_addresses_returns_results(self):
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)
        address = make_address(user_id=user.id)
        fake_db = FakeDb([_ExecResult(scalar_list=[address])])

        result = await users_router.list_addresses(user_id=user.id, db=fake_db)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].city, "Istanbul")

    async def test_create_address_adds_to_db(self):
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)
        new_id = uuid4()
        fake_db = FakeDb([], refresh_attrs={
            "id": new_id,
            "address_title": "Home",
            "city": "Istanbul",
            "district": "Kadikoy",
            "neighborhood": "Moda",
            "street": "Main St",
            "building_no": "5",
            "floor": "3",
            "apartment_no": "7",
            "address_description": None,
            "phone": "5551234567",
            "lat": None,
            "lng": None,
        })
        payload = AddressCreate(
            address_title="Home",
            city="Istanbul",
            district="Kadikoy",
            neighborhood="Moda",
            street="Main St",
            building_no="5",
            floor="3",
            apartment_no="7",
            phone="5551234567",
        )

        response = await users_router.create_address(
            payload=payload, user_id=user.id, db=fake_db
        )

        self.assertEqual(len(fake_db.added), 1)
        self.assertEqual(fake_db.commits, 1)
        self.assertEqual(response.city, "Istanbul")

    async def test_update_address_updates_city(self):
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)
        address = make_address(user_id=user.id)
        fake_db = FakeDb([_ExecResult(scalar=address)])

        async def _noop_refresh(item):
            pass

        fake_db.refresh = _noop_refresh

        await users_router.update_address(
            payload=AddressUpdate(city="Ankara"),
            address_id=f"addr_{address.id}",
            user_id=user.id,
            db=fake_db,
        )

        self.assertEqual(address.city, "Ankara")
        self.assertEqual(fake_db.commits, 1)

    async def test_update_address_not_found_raises_404(self):
        from fastapi import HTTPException
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)
        fake_db = FakeDb([_ExecResult(scalar=None)])

        with self.assertRaises(HTTPException) as ctx:
            await users_router.update_address(
                payload=AddressUpdate(city="Ankara"),
                address_id=f"addr_{uuid4()}",
                user_id=user.id,
                db=fake_db,
            )

        self.assertEqual(ctx.exception.status_code, 404)

    async def test_delete_address_soft_deletes(self):
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)
        address = make_address(user_id=user.id)
        fake_db = FakeDb([_ExecResult(scalar=address)])

        response = await users_router.delete_address(
            address_id=f"addr_{address.id}",
            user_id=user.id,
            db=fake_db,
        )

        self.assertEqual(response.message, "Address deleted")
        self.assertIsNotNone(address.deleted_at)
        self.assertFalse(address.is_current)
        self.assertEqual(fake_db.commits, 1)

    async def test_delete_address_not_found_raises_404(self):
        from fastapi import HTTPException
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)
        fake_db = FakeDb([_ExecResult(scalar=None)])

        with self.assertRaises(HTTPException) as ctx:
            await users_router.delete_address(
                address_id=f"addr_{uuid4()}",
                user_id=user.id,
                db=fake_db,
            )

        self.assertEqual(ctx.exception.status_code, 404)

    async def test_set_current_address_marks_target(self):
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)
        address = make_address(user_id=user.id, is_current=False)
        fake_db = FakeDb([_ExecResult(scalar=address), _ExecResult()])

        response = await users_router.set_current_address(
            address_id=f"addr_{address.id}",
            user_id=user.id,
            db=fake_db,
        )

        self.assertEqual(response.message, "Current address updated")
        self.assertTrue(address.is_current)
        self.assertEqual(fake_db.commits, 1)

    async def test_set_current_address_not_found_raises_404(self):
        from fastapi import HTTPException
        user = make_user()
        users_router.get_current_user = AsyncMock(return_value=user)
        fake_db = FakeDb([_ExecResult(scalar=None)])

        with self.assertRaises(HTTPException) as ctx:
            await users_router.set_current_address(
                address_id=f"addr_{uuid4()}",
                user_id=user.id,
                db=fake_db,
            )

        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
