import unittest

from auth import create_password_record, verify_password
from security import validate_request_id


class TestNoteSecured(unittest.TestCase):
    def test_password_hashing(self):
        record = create_password_record("mypassword123")
        self.assertIn("salt", record)
        self.assertIn("password_hash", record)
        self.assertTrue(verify_password("mypassword123", record["salt"], record["password_hash"]))
        self.assertFalse(verify_password("wrongpass", record["salt"], record["password_hash"]))

    def test_replay_detection(self):
        request_id = "fixed-request-id-123"
        self.assertTrue(validate_request_id(request_id))
        self.assertFalse(validate_request_id(request_id))


if __name__ == "__main__":
    unittest.main()