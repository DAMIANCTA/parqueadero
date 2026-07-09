import unittest

from services.member_access_service import MemberAccessService
from schemas.members import MemberAccessValidationRequest


class MemberAccessServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = MemberAccessService()

    def test_registered_member_plate_returns_member_authorized(self) -> None:
        payload = MemberAccessValidationRequest(
            university_id="11111111-1111-1111-1111-111111111111",
            plate_text="ABC1234",
            face_image_id="face-valid-001",
            gate_id="gate-north",
        )

        response = self.service.validate_member_access(payload)

        self.assertTrue(response.authorized)
        self.assertEqual(response.access_type, "MEMBER")
        self.assertEqual(response.role_type, "STUDENT")

    def test_unknown_plate_returns_not_registered(self) -> None:
        payload = MemberAccessValidationRequest(
            university_id="11111111-1111-1111-1111-111111111111",
            plate_text="ZZZ0001",
            face_image_id="face-valid-002",
            gate_id="gate-north",
        )

        response = self.service.validate_member_access(payload)

        self.assertFalse(response.authorized)
        self.assertFalse(response.vehicle_registered)


if __name__ == "__main__":
    unittest.main()
