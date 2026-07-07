import unittest
from copy import deepcopy

from fastapi.testclient import TestClient

from config import settings
from main import app
from repositories.payment_repository import PaymentRepository
from security import encode_access_token


class PaymentFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        PaymentRepository.sessions = deepcopy(PaymentRepository.INITIAL_SESSIONS)
        token = encode_access_token(
            secret_key=settings.jwt_secret_key,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            expires_minutes=30,
            claims={
                "sub": "test-cashier",
                "username": "cashier.user",
                "roles": ["cashier"],
                "permissions": ["payments.read", "payments.pay"],
                "university_id": "11111111-1111-1111-1111-111111111111",
            },
        )
        self.headers = {"Authorization": f"Bearer {token}"}

    def test_find_session_by_plate(self) -> None:
        response = self.client.get("/payments/session/VIS1234", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["found"])
        self.assertEqual(payload["session"]["plate_text"], "VIS1234")
        self.assertGreater(payload["session"]["amount_due"], 0)

    def test_find_session_by_qr(self) -> None:
        response = self.client.get("/payments/session-by-qr/QR-VISPEND", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["found"])
        self.assertEqual(payload["session"]["qr_code"], "QR-VISPEND")

    def test_pay_session_marks_status_paid(self) -> None:
        response = self.client.post(
            "/payments/pay",
            headers=self.headers,
            json={
                "session_id": "session-visitor-pending-001",
                "cashier_user_id": "cashier-007",
                "payment_method": "card",
                "amount": 1.50,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["session"]["payment_status"], "PAID")
        self.assertEqual(payload["session"]["cashier_user_id"], "cashier-007")
        self.assertEqual(payload["session"]["payment_method"], "card")
        self.assertIsNotNone(payload["session"]["paid_at"])

    def test_get_payment_status(self) -> None:
        response = self.client.get("/payments/status/session-visitor-done-001", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["found"])
        self.assertEqual(payload["payment_status"], "PAID")

    def test_pay_by_plate_marks_pending_session_as_paid(self) -> None:
        response = self.client.post(
            "/payments/pay-by-plate",
            headers=self.headers,
            json={
                "plate_text": "VISPEND",
                "cashier_user_id": "cashier-demo",
                "payment_method": "cash",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["session"]["plate_text"], "VISPEND")
        self.assertEqual(payload["session"]["payment_status"], "PAID")
        self.assertEqual(payload["session"]["cashier_user_id"], "cashier-demo")

    def test_cashier_lookup_by_plate_returns_active_inside_session(self) -> None:
        response = self.client.get("/payments/by-plate/VISPEND", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["found"])
        self.assertEqual(payload["plate_text"], "VISPEND")
        self.assertEqual(payload["payment_status"], "PENDING")
        self.assertGreaterEqual(payload["duration_minutes"], 1)

    def test_register_cash_payment_marks_session_paid_and_receipt(self) -> None:
        response = self.client.post(
            "/payments/register-cash-payment",
            headers=self.headers,
            json={
                "session_id": "session-visitor-pending-001",
                "plate_text": "VISPEND",
                "amount": 1.50,
                "payment_method": "cash",
                "cashier_user_id": "cashier.user",
                "notes": "Pago en secretaria",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["session"]["found"])
        self.assertEqual(payload["session"]["payment_status"], "PAID")
        self.assertTrue(payload["receipt_number"].startswith("REC-"))
        self.assertIsNotNone(payload["paid_at"])
        self.assertEqual(payload["session"]["amount"], payload["session"]["paid_amount"])
        self.assertIsNotNone(payload["session"]["payment_valid_until"])

    def test_register_cash_payment_rejects_double_payment(self) -> None:
        response = self.client.post(
            "/payments/register-cash-payment",
            headers=self.headers,
            json={
                "session_id": "session-visitor-done-001",
                "plate_text": "VISDONE",
                "amount": 1.50,
                "payment_method": "cash",
                "cashier_user_id": "cashier.user",
                "notes": "Segundo intento",
            },
        )

        self.assertEqual(response.status_code, 409)

    def test_lookup_returns_not_found_for_outside_session(self) -> None:
        response = self.client.get("/payments/by-plate/VISDONE", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["found"])
        self.assertEqual(payload["message"], "No active session found for this plate")


if __name__ == "__main__":
    unittest.main()
