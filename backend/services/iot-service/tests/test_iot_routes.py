import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from config import settings
from main import app
from security import encode_access_token


class IoTRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        token = encode_access_token(
            secret_key=settings.jwt_secret_key,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            expires_minutes=30,
            claims={
                "sub": "test-iot-admin",
                "username": "iot.admin",
                "roles": ["admin_university"],
                "permissions": ["iot.gates.open", "iot.gates.deny", "iot.gates.read"],
                "university_id": "uce",
            },
        )
        self.headers = {"Authorization": f"Bearer {token}"}

    @patch("routes.iot.mqtt_service.open_gate")
    def test_open_gate_publishes_expected_command(self, open_gate) -> None:
        open_gate.return_value = {
            "gate_id": "garita-01",
            "status": "OPENED",
            "command": "open",
            "command_code": "ABRIR",
            "published": True,
            "topic": "ucepark/garita/comandos",
            "mqtt_connected": True,
            "payload": "ABRIR",
            "event_topic": "ucepark/garita/eventos",
            "timestamp": "2026-07-09T12:00:00+00:00",
            "reason": "validated",
        }
        response = self.client.post(
            "/gates/garita-01/open",
            headers=self.headers,
            json={
                "university_id": "uce",
                "campus_id": "matriz",
                "plate": "ABC1234",
                "session_id": "session-demo-001",
                "reason": "validated",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["published"])
        self.assertEqual(payload["command_code"], "ABRIR")
        self.assertEqual(payload["topic"], "ucepark/garita/comandos")
        open_gate.assert_called_once()

    @patch("routes.iot.mqtt_service.deny_gate")
    def test_deny_gate_publishes_expected_command(self, deny_gate) -> None:
        deny_gate.return_value = {
            "gate_id": "garita-01",
            "status": "DENIED",
            "command": "deny",
            "command_code": "DENEGAR",
            "published": True,
            "topic": "ucepark/garita/comandos",
            "mqtt_connected": True,
            "payload": "DENEGAR",
            "event_topic": "ucepark/garita/eventos",
            "timestamp": "2026-07-09T12:00:00+00:00",
            "reason": "payment_pending",
        }
        response = self.client.post(
            "/gates/garita-01/deny",
            headers=self.headers,
            json={
                "university_id": "uce",
                "campus_id": "matriz",
                "plate": "ABC1234",
                "session_id": "session-demo-001",
                "reason": "payment_pending",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["command_code"], "DENEGAR")
        self.assertEqual(payload["status"], "DENIED")
        deny_gate.assert_called_once()

    @patch("routes.iot.mqtt_service.get_gate_status")
    def test_status_route_returns_gate_runtime_status(self, get_gate_status) -> None:
        get_gate_status.return_value = {
            "gate_id": "garita-01",
            "status": "PRESENCE_DETECTED",
            "mqtt_connected": True,
            "command_topic": "ucepark/garita/comandos",
            "event_topic": "ucepark/garita/eventos",
            "last_event_type": "PRESENCE_DETECTED",
            "last_event_payload": "PRESENCIA",
            "last_presence_at": "2026-07-09T12:00:00+00:00",
            "last_command": "ABRIR",
            "last_command_at": "2026-07-09T11:59:00+00:00",
            "last_updated_at": "2026-07-09T12:00:00+00:00",
            "last_reason": "validated",
            "university_id": "uce",
            "campus_id": "matriz",
            "plate": "ABC1234",
            "session_id": "session-demo-001",
        }
        response = self.client.get("/gates/garita-01/status", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "PRESENCE_DETECTED")
        self.assertTrue(payload["mqtt_connected"])
        self.assertEqual(payload["event_topic"], "ucepark/garita/eventos")
        get_gate_status.assert_called_once_with("garita-01")


if __name__ == "__main__":
    unittest.main()
