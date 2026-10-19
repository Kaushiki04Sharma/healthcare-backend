from config.testing import AuthAPITestCase
from patients.models import Patient


class PatientTests(AuthAPITestCase):
    def setUp(self):
        self.owner = self.make_user("owner@example.com")
        self.other = self.make_user("other@example.com")
        self.client_owner = self.client_for(self.owner)
        self.client_other = self.client_for(self.other)

    def test_create_patient_sets_owner(self):
        response = self.client_owner.post(
            "/api/patients/", self.patient_payload(phone="+91 98765-43210"), format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Patient.objects.get(pk=response.data["id"]).created_by, self.owner)

    def test_create_validation_errors(self):
        response = self.client_owner.post(
            "/api/patients/", {"name": "  ", "age": 200, "gender": "robot"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        details = response.data["error"]["details"]
        for field in ("name", "age", "gender"):
            self.assertIn(field, details)

    def test_invalid_phone_rejected(self):
        response = self.client_owner.post(
            "/api/patients/", self.patient_payload(phone="abc"), format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_list_returns_only_own_patients(self):
        self.client_owner.post("/api/patients/", self.patient_payload(name="Mine"), format="json")
        self.client_other.post("/api/patients/", self.patient_payload(name="Theirs"), format="json")
        response = self.client_owner.get("/api/patients/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p["name"] for p in response.data], ["Mine"])

    def test_retrieve_update_delete_own_patient(self):
        pid = self.client_owner.post(
            "/api/patients/", self.patient_payload(), format="json"
        ).data["id"]

        self.assertEqual(self.client_owner.get(f"/api/patients/{pid}/").status_code, 200)

        put = self.client_owner.put(
            f"/api/patients/{pid}/",
            self.patient_payload(name="Ravi Kumar", age=31),
            format="json",
        )
        self.assertEqual(put.status_code, 200)
        self.assertEqual(put.data["name"], "Ravi Kumar")
        self.assertEqual(put.data["age"], 31)

        self.assertEqual(self.client_owner.delete(f"/api/patients/{pid}/").status_code, 204)
        self.assertEqual(self.client_owner.get(f"/api/patients/{pid}/").status_code, 404)

    def test_other_user_cannot_access_patient(self):
        pid = self.client_owner.post(
            "/api/patients/", self.patient_payload(), format="json"
        ).data["id"]
        url = f"/api/patients/{pid}/"
        self.assertEqual(self.client_other.get(url).status_code, 404)
        self.assertEqual(
            self.client_other.put(url, self.patient_payload(name="Hacked"), format="json").status_code,
            404,
        )
        self.assertEqual(self.client_other.delete(url).status_code, 404)
        self.assertEqual(Patient.objects.get(pk=pid).name, "Ravi")

    def test_missing_patient_404_uses_error_format(self):
        response = self.client_owner.get("/api/patients/9999/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error"]["status_code"], 404)
