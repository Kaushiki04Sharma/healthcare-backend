"""Shared helpers for the test suites."""
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase

PASSWORD = "Str0ngPass!23"


class AuthAPITestCase(APITestCase):
    """Base class with helpers to create users and authenticated clients."""

    def make_user(self, email="user@example.com", name="Test User"):
        return User.objects.create_user(
            username=email, email=email, first_name=name, password=PASSWORD
        )

    def client_for(self, user):
        """Return an APIClient authenticated through the real login endpoint."""
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return client

    # Payload factories -------------------------------------------------
    @staticmethod
    def patient_payload(**overrides):
        data = {"name": "Ravi", "age": 30, "gender": "male"}
        data.update(overrides)
        return data

    @staticmethod
    def doctor_payload(**overrides):
        data = {
            "name": "Meera",
            "specialization": "Cardiology",
            "email": "meera@example.com",
            "experience_years": 8,
        }
        data.update(overrides)
        return data
