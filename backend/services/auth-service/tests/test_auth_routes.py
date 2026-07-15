import unittest

from fastapi.testclient import TestClient

from main import app


class AuthRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_login_returns_user_payload_and_uppercase_role(self) -> None:
        response = self.client.post(
            "/auth/login",
            json={"username": "admin.university", "password": "demo1234!"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["token_type"], "bearer")
        self.assertEqual(body["user"]["role"], "UNIVERSITY_ADMIN")
        self.assertEqual(body["user"]["username"], "admin.university")
        self.assertEqual(body["roles"], ["UNIVERSITY_ADMIN"])

    def test_me_requires_bearer_token(self) -> None:
        response = self.client.get("/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_users_requires_authentication(self) -> None:
        response = self.client.get("/users")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
