import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from config import settings
from main import app
from security import encode_access_token


class GatewayRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
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

    @patch("routes.system.integration_service.collect_health")
    def test_health_returns_aggregated_checks(self, collect_health) -> None:
        collect_health.return_value = [
            {"name": "parking-service", "status": "ok", "detail": "ok"},
            {"name": "mqtt", "status": "ok", "detail": "ok"},
        ]

        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(len(body["checks"]), 2)

    @patch("routes.integration.integration_service.open_demo_gate")
    def test_demo_open_gate_returns_payload(self, open_demo_gate) -> None:
        open_demo_gate.return_value = {
            "status": "OPEN_COMMAND_SENT",
            "message": "La barrera demo fue enviada a abrir.",
            "demo_event_id": "demo-123",
            "topic": "universities/uce/campuses/matriz/gates/norte/cmd",
            "status_topic": "universities/uce/campuses/matriz/gates/norte/status",
            "command": "open",
            "published": True,
            "payload": {
                "command": "open",
                "plate": "ABC1234",
                "session_id": "demo-123",
                "reason": "demo_validated",
            },
        }

        response = self.client.post(
            "/demo/open-gate",
            json={
                "university_id": "uce",
                "campus_id": "matriz",
                "gate_id": "norte",
                "plate": "ABC1234",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "OPEN_COMMAND_SENT")
        self.assertTrue(body["published"])

    @patch("routes.integration.integration_service.get_payment_by_plate")
    def test_get_payment_by_plate_is_available_for_operational_check(self, get_payment_by_plate) -> None:
        get_payment_by_plate.return_value = {
            "found": True,
            "message": "Sesion activa encontrada",
            "session_id": "session-visitor-pending-001",
            "plate_text": "VISPEND",
            "entry_time": "2026-07-07T20:00:00Z",
            "duration_minutes": 45,
            "amount": 1.5,
            "currency": "USD",
            "payment_status": "PENDING",
        }

        response = self.client.get("/payments/by-plate/VISPEND")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["found"])
        self.assertEqual(body["plate_text"], "VISPEND")
        self.assertEqual(body["payment_status"], "PENDING")

    @patch("routes.integration.integration_service.register_cash_payment")
    def test_register_cash_payment_requires_authenticated_cashier(self, register_cash_payment) -> None:
        register_cash_payment.return_value = {
            "success": True,
            "message": "Cash payment registered successfully",
            "receipt_number": "REC-20260707-0002",
            "paid_at": "2026-07-07T20:10:31Z",
            "audit_log_id": "audit-123",
            "session": {
                "found": True,
                "message": "Pago registrado",
                "session_id": "session-visitor-pending-001",
                "plate_text": "VISPEND",
                "entry_time": "2026-07-07T20:00:00Z",
                "session_status": "INSIDE",
                "duration_minutes": 45,
                "amount": 1.5,
                "currency": "USD",
                "payment_status": "PAID",
                "paid_at": "2026-07-07T20:10:31Z",
                "paid_amount": 1.5,
                "payment_method": "cash",
                "payment_valid_until": "2026-07-07T20:25:31Z",
                "receipt_number": "REC-20260707-0002",
            },
        }

        unauthorized = self.client.post(
            "/payments/register-cash-payment",
            json={
                "session_id": "session-visitor-pending-001",
                "plate_text": "VISPEND",
                "amount": 1.5,
                "payment_method": "cash",
                "cashier_user_id": "cashier.user",
                "notes": "Pago en secretaria",
            },
        )
        self.assertEqual(unauthorized.status_code, 401)

        authorized = self.client.post(
            "/payments/register-cash-payment",
            headers=self.headers,
            json={
                "session_id": "session-visitor-pending-001",
                "plate_text": "VISPEND",
                "amount": 1.5,
                "payment_method": "cash",
                "cashier_user_id": "cashier.user",
                "notes": "Pago en secretaria",
            },
        )

        self.assertEqual(authorized.status_code, 200)
        body = authorized.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["session"]["payment_status"], "PAID")


if __name__ == "__main__":
    unittest.main()
