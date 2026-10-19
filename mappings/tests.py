from config.testing import AuthAPITestCase
from mappings.models import PatientDoctorMapping


class MappingTests(AuthAPITestCase):
    def setUp(self):
        self.owner = self.make_user("owner@example.com")
        self.other = self.make_user("other@example.com")
        self.client_owner = self.client_for(self.owner)
        self.client_other = self.client_for(self.other)

        self.patient_id = self.client_owner.post(
            "/api/patients/", self.patient_payload(), format="json"
        ).data["id"]
        self.doctor_id = self.client_owner.post(
            "/api/doctors/", self.doctor_payload(), format="json"
        ).data["id"]

    def assign(self, client=None, patient=None, doctor=None):
        client = client or self.client_owner
        return client.post(
            "/api/mappings/",
            {"patient": patient or self.patient_id, "doctor": doctor or self.doctor_id},
            format="json",
        )

    def test_assign_doctor_to_patient(self):
        response = self.assign()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["patient_name"], "Ravi")
        self.assertEqual(response.data["doctor_name"], "Meera")
        self.assertEqual(PatientDoctorMapping.objects.get().assigned_by, self.owner)

    def test_duplicate_assignment_rejected(self):
        self.assertEqual(self.assign().status_code, 201)
        self.assertEqual(self.assign().status_code, 400)
        self.assertEqual(PatientDoctorMapping.objects.count(), 1)

    def test_nonexistent_patient_or_doctor(self):
        self.assertEqual(self.assign(patient=9999).status_code, 400)
        self.assertEqual(self.assign(doctor=9999).status_code, 400)

    def test_missing_fields(self):
        response = self.client_owner.post("/api/mappings/", {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_cannot_assign_to_someone_elses_patient(self):
        response = self.assign(client=self.client_other)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(PatientDoctorMapping.objects.count(), 0)

    def test_list_only_own_patients_mappings(self):
        self.assign()
        self.assertEqual(len(self.client_owner.get("/api/mappings/").data), 1)
        self.assertEqual(len(self.client_other.get("/api/mappings/").data), 0)

    def test_doctors_for_patient(self):
        self.assign()
        response = self.client_owner.get(f"/api/mappings/{self.patient_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["patient"]["id"], self.patient_id)
        doctors = response.data["doctors"]
        self.assertEqual(len(doctors), 1)
        self.assertEqual(doctors[0]["doctor"]["name"], "Meera")
        self.assertEqual(doctors[0]["doctor"]["specialization"], "Cardiology")

    def test_doctors_for_other_users_patient_is_404(self):
        self.assign()
        response = self.client_other.get(f"/api/mappings/{self.patient_id}/")
        self.assertEqual(response.status_code, 404)

    def test_remove_assignment(self):
        mapping_id = self.assign().data["id"]
        self.assertEqual(
            self.client_owner.delete(f"/api/mappings/{mapping_id}/").status_code, 204
        )
        response = self.client_owner.get(f"/api/mappings/{self.patient_id}/")
        self.assertEqual(response.data["doctors"], [])

    def test_cannot_remove_someone_elses_mapping(self):
        mapping_id = self.assign().data["id"]
        response = self.client_other.delete(f"/api/mappings/{mapping_id}/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(PatientDoctorMapping.objects.count(), 1)

    def test_deleting_patient_removes_its_mappings(self):
        self.assign()
        self.client_owner.delete(f"/api/patients/{self.patient_id}/")
        self.assertEqual(PatientDoctorMapping.objects.count(), 0)
