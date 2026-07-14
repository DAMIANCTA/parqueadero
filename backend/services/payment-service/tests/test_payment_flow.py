import unittest
from datetime import datetime, UTC

from fastapi.testclient import TestClient

from config import settings
from main import app
from repositories.payment_repository import PaymentRepository
from security import encode_access_token


class PaymentFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        PaymentRepository.reset()
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

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["detail"], "No hay una sesion activa para esta placa")

    def test_payment_search_ignores_old_outside_sessions(self) -> None:
        repository = PaymentRepository()
        repository.sessions["session-old-paid-002"] = {
            "session_id": "session-old-paid-002",
            "plate_text": "MCB250",
            "qr_code": "QR-MCB250-A",
            "entry_time": datetime.now(UTC),
            "exit_time": datetime.now(UTC),
            "session_status": "OUTSIDE",
            "access_type": "VISITOR",
            "payment_status": "PAID",
            "cashier_user_id": "cashier-001",
            "amount": 1.50,
            "paid_amount": 1.50,
            "payment_method": "cash",
            "paid_at": datetime.now(UTC),
            "payment_valid_until": datetime.now(UTC),
            "receipt_number": "REC-OLD-0001",
            "notes": "Sesion historica",
            "currency": "USD",
        }
        repository.upsert_session("session-current-pending-002", "MCB250", "PENDING", "VISITOR")

        response = self.client.get("/payments/by-plate/MCB250", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["session_id"], "session-current-pending-002")
        self.assertEqual(payload["payment_status"], "PENDING")
        self.assertEqual(payload["access_type"], "VISITOR")

    def test_payment_register_requires_active_inside_session(self) -> None:
        response = self.client.post(
            "/payments/register-cash-payment",
            headers=self.headers,
            json={
                "session_id": "session-visitor-done-001",
                "plate_text": "VISDONE",
                "amount": 1.50,
                "payment_method": "cash",
                "cashier_user_id": "cashier.user",
                "notes": "Pago tardio",
            },
        )

        self.assertEqual(response.status_code, 409)
        payload = response.json()
        self.assertEqual(payload["detail"], "La sesion ya fue cerrada")

    def test_member_not_required_is_not_cashier_payment(self) -> None:
        repository = PaymentRepository()
        repository.upsert_session("session-member-001", "MEM250", "NOT_REQUIRED", "MEMBER")

        lookup_response = self.client.get("/payments/by-plate/MEM250", headers=self.headers)
        self.assertEqual(lookup_response.status_code, 404)

        payment_response = self.client.post(
            "/payments/register-cash-payment",
            headers=self.headers,
            json={
                "session_id": "session-member-001",
                "plate_text": "MEM250",
                "amount": 0.0 + 1.5,
                "payment_method": "cash",
                "cashier_user_id": "cashier.user",
                "notes": "No deberia cobrar",
            },
        )

        self.assertEqual(payment_response.status_code, 409)
        payload = payment_response.json()
        self.assertEqual(payload["detail"], "Pago no requerido para miembro universitario")

    def test_visitor_can_pay_again_after_reentry(self) -> None:
        repository = PaymentRepository()
        repository.upsert_session("session-reentry-a", "MCB250", "PENDING", "VISITOR")

        first_payment = self.client.post(
            "/payments/register-cash-payment",
            headers=self.headers,
            json={
                "session_id": "session-reentry-a",
                "plate_text": "MCB250",
                "amount": 1.50,
                "payment_method": "cash",
                "cashier_user_id": "cashier.user",
                "notes": "Primer pago",
            },
        )
        self.assertEqual(first_payment.status_code, 200)

        repository.close_session(
            session_id="session-reentry-a",
            plate_text="MCB250",
            payment_status="PAID",
            exit_time=datetime.now(UTC),
        )
        repository.upsert_session("session-reentry-b", "MCB250", "PENDING", "VISITOR")

        lookup = self.client.get("/payments/by-plate/MCB250", headers=self.headers)
        self.assertEqual(lookup.status_code, 200)
        lookup_payload = lookup.json()
        self.assertEqual(lookup_payload["session_id"], "session-reentry-b")
        self.assertEqual(lookup_payload["payment_status"], "PENDING")

        second_payment = self.client.post(
            "/payments/register-cash-payment",
            headers=self.headers,
            json={
                "session_id": "session-reentry-b",
                "plate_text": "MCB250",
                "amount": 1.50,
                "payment_method": "cash",
                "cashier_user_id": "cashier.user",
                "notes": "Segundo pago",
            },
        )
        self.assertEqual(second_payment.status_code, 200)
        second_payload = second_payment.json()
        self.assertEqual(second_payload["session"]["session_id"], "session-reentry-b")
        self.assertEqual(second_payload["session"]["payment_status"], "PAID")

    def test_admin_dashboard_summary_returns_operational_totals(self) -> None:
        response = self.client.get("/payments/admin/dashboard-summary", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(payload["active_sessions"], 1)
        self.assertIn("revenue_today", payload)

    def test_admin_session_lists_split_inside_and_outside(self) -> None:
        active_response = self.client.get("/payments/admin/active-sessions", headers=self.headers)
        history_response = self.client.get("/payments/admin/session-history", headers=self.headers)

        self.assertEqual(active_response.status_code, 200)
        self.assertEqual(history_response.status_code, 200)
        active_payload = active_response.json()
        history_payload = history_response.json()
        self.assertTrue(any(item["session_status"] == "INSIDE" for item in active_payload["items"]))
        self.assertTrue(any(item["session_status"] == "OUTSIDE" for item in history_payload["items"]))


if __name__ == "__main__":
    unittest.main()
