import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


class IoTRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    @patch("repositories.mqtt_repository.publish.single")
    def test_open_gate_publishes_expected_topic(self, publish_single) -> None:
        response = self.client.post(
            "/api/v1/gates/open",
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "campus_id": "22222222-2222-2222-2222-222222222222",
                "gate_id": "33333333-3333-3333-3333-333333333331",
                "plate": "ABC1234",
                "session_id": "session-demo-001",
                "reason": "validated",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["published"])
        self.assertEqual(payload["command"], "open")
        self.assertEqual(
            payload["topic"],
            "universities/11111111-1111-1111-1111-111111111111/campuses/22222222-2222-2222-2222-222222222222/gates/33333333-3333-3333-3333-333333333331/cmd",
        )
        self.assertEqual(
            payload["status_topic"],
            "universities/11111111-1111-1111-1111-111111111111/campuses/22222222-2222-2222-2222-222222222222/gates/33333333-3333-3333-3333-333333333331/status",
        )
        publish_single.assert_called_once()


if __name__ == "__main__":
    unittest.main()
