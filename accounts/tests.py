from django.contrib.auth.models import User
from rest_framework.test import APIClient

from config.testing import PASSWORD, AuthAPITestCase


class RegisterTests(AuthAPITestCase):
    url = "/api/auth/register/"

    def test_register_success(self):
        response = APIClient().post(
            self.url,
            {"name": "Asha", "email": "Asha@Example.com", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"]["email"], "asha@example.com")
        self.assertEqual(response.data["user"]["name"], "Asha")
        self.assertNotIn("password", response.data["user"])
        user = User.objects.get(email="asha@example.com")
        self.assertTrue(user.check_password(PASSWORD))  # stored hashed

    def test_duplicate_email_rejected_case_insensitive(self):
        self.make_user("asha@example.com")
        response = APIClient().post(
            self.url,
            {"name": "Asha 2", "email": "ASHA@example.com", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data["error"]["details"])

    def test_missing_fields(self):
        response = APIClient().post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data["error"]["details"]
        for field in ("name", "email", "password"):
            self.assertIn(field, details)

    def test_invalid_email(self):
        response = APIClient().post(
            self.url,
            {"name": "A", "email": "not-an-email", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_weak_password_rejected(self):
        response = APIClient().post(
            self.url,
            {"name": "A", "email": "a@example.com", "password": "password"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data["error"]["details"])


class LoginTests(AuthAPITestCase):
    url = "/api/auth/login/"

    def test_login_success_returns_tokens(self):
        user = self.make_user("asha@example.com", "Asha")
        response = APIClient().post(
            self.url, {"email": user.email, "password": PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_email_is_case_insensitive(self):
        self.make_user("asha@example.com")
        response = APIClient().post(
            self.url, {"email": "ASHA@example.com", "password": PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_wrong_password(self):
        user = self.make_user()
        response = APIClient().post(
            self.url, {"email": user.email, "password": "WrongPass!99"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_user(self):
        response = APIClient().post(
            self.url, {"email": "nobody@example.com", "password": PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_refresh_token_returns_new_access(self):
        user = self.make_user()
        login = APIClient().post(
            self.url, {"email": user.email, "password": PASSWORD}, format="json"
        )
        response = APIClient().post(
            "/api/auth/token/refresh/", {"refresh": login.data["refresh"]}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)


class ProtectedEndpointTests(AuthAPITestCase):
    def test_endpoints_require_authentication(self):
        client = APIClient()
        for url in ("/api/patients/", "/api/doctors/", "/api/mappings/"):
            response = client.get(url)
            self.assertEqual(response.status_code, 401, url)

    def test_invalid_token_rejected(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")
        self.assertEqual(client.get("/api/patients/").status_code, 401)
