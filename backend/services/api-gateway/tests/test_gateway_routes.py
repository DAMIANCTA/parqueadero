import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


class GatewayRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

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


if __name__ == "__main__":
    unittest.main()
