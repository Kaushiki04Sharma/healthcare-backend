from config.testing import AuthAPITestCase


class DoctorTests(AuthAPITestCase):
    def setUp(self):
        self.creator = self.make_user("creator@example.com")
        self.other = self.make_user("other@example.com")
        self.client_creator = self.client_for(self.creator)
        self.client_other = self.client_for(self.other)

    def test_create_doctor(self):
        response = self.client_creator.post(
            "/api/doctors/", self.doctor_payload(email="Meera@Example.com"), format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["email"], "meera@example.com")

    def test_duplicate_email_rejected(self):
        self.client_creator.post("/api/doctors/", self.doctor_payload(), format="json")
        response = self.client_other.post(
            "/api/doctors/", self.doctor_payload(name="Another"), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data["error"]["details"])

    def test_validation_errors(self):
        response = self.client_creator.post(
            "/api/doctors/", {"name": "", "email": "bad"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        details = response.data["error"]["details"]
        for field in ("name", "specialization", "email"):
            self.assertIn(field, details)

    def test_all_users_can_list_and_retrieve_doctors(self):
        did = self.client_creator.post(
            "/api/doctors/", self.doctor_payload(), format="json"
        ).data["id"]
        listing = self.client_other.get("/api/doctors/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data), 1)
        self.assertEqual(self.client_other.get(f"/api/doctors/{did}/").status_code, 200)

    def test_creator_can_update_and_delete(self):
        did = self.client_creator.post(
            "/api/doctors/", self.doctor_payload(), format="json"
        ).data["id"]
        put = self.client_creator.put(
            f"/api/doctors/{did}/",
            self.doctor_payload(specialization="Neurology"),
            format="json",
        )
        self.assertEqual(put.status_code, 200)
        self.assertEqual(put.data["specialization"], "Neurology")
        self.assertEqual(self.client_creator.delete(f"/api/doctors/{did}/").status_code, 204)

    def test_updating_own_doctor_keeps_same_email(self):
        did = self.client_creator.post(
            "/api/doctors/", self.doctor_payload(), format="json"
        ).data["id"]
        response = self.client_creator.put(
            f"/api/doctors/{did}/", self.doctor_payload(name="Meera K"), format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_non_creator_cannot_modify(self):
        did = self.client_creator.post(
            "/api/doctors/", self.doctor_payload(), format="json"
        ).data["id"]
        url = f"/api/doctors/{did}/"
        self.assertEqual(
            self.client_other.put(url, self.doctor_payload(name="Hacked"), format="json").status_code,
            403,
        )
        self.assertEqual(self.client_other.delete(url).status_code, 403)
        self.assertEqual(self.client_creator.get(url).data["name"], "Meera")
