import unittest

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from ._test_helpers import users_router, SKIP_REASON

_SKIP = unittest.skipIf(users_router is None, SKIP_REASON or "")


@_SKIP
class MaskPhoneTests(unittest.TestCase):
    def test_standard_10_digit_phone(self):
        result = users_router.mask_phone("5551234567")
        self.assertEqual(result[:3], "555")
        self.assertIn("*", result)
        self.assertEqual(result[-2:], "67")

    def test_short_phone_returned_unchanged(self):
        result = users_router.mask_phone("1234")
        self.assertEqual(result, "1234")

    def test_phone_with_separators(self):
        result = users_router.mask_phone("+90 555 123 45 67")
        self.assertIn("*", result)
        self.assertNotIn(" ", result)


@_SKIP
class AddressIdHelperTests(unittest.TestCase):
    def test_format_and_parse_round_trip(self):
        from uuid import uuid4
        original = uuid4()
        formatted = users_router.format_address_id(original)
        self.assertTrue(formatted.startswith("addr_"))
        self.assertEqual(users_router.parse_address_id(formatted), original)

    def test_parse_without_prefix(self):
        from uuid import uuid4
        uid = uuid4()
        self.assertEqual(users_router.parse_address_id(str(uid)), uid)

    def test_parse_invalid_raises_400(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            users_router.parse_address_id("not-a-uuid")
        self.assertEqual(ctx.exception.status_code, 400)


@_SKIP
class HashResetTokenTests(unittest.TestCase):
    def test_deterministic(self):
        token = "my_secret_token"
        self.assertEqual(
            users_router.hash_reset_token(token),
            users_router.hash_reset_token(token),
        )

    def test_different_inputs_produce_different_hashes(self):
        self.assertNotEqual(
            users_router.hash_reset_token("token_a"),
            users_router.hash_reset_token("token_b"),
        )


if __name__ == "__main__":
    unittest.main()
