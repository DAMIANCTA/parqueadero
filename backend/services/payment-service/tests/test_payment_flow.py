import unittest

from fastapi.testclient import TestClient

from main import app


class PaymentFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_find_session_by_plate(self) -> None:
        response = self.client.get("/payments/session/VIS1234")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["found"])
        self.assertEqual(payload["session"]["plate_text"], "VIS1234")
        self.assertGreater(payload["session"]["amount_due"], 0)

    def test_find_session_by_qr(self) -> None:
        response = self.client.get("/payments/session-by-qr/QR-VISPEND")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["found"])
        self.assertEqual(payload["session"]["qr_code"], "QR-VISPEND")

    def test_pay_session_marks_status_paid(self) -> None:
        response = self.client.post(
            "/payments/pay",
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
        response = self.client.get("/payments/status/session-visitor-done-001")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["found"])
        self.assertEqual(payload["payment_status"], "PAID")

    def test_pay_by_plate_marks_pending_session_as_paid(self) -> None:
        response = self.client.post(
            "/payments/pay-by-plate",
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


if __name__ == "__main__":
    unittest.main()
