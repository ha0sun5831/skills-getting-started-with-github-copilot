import unittest
from copy import deepcopy

from fastapi.testclient import TestClient

from src.app import activities, app


class UnregisterTests(unittest.TestCase):
    def setUp(self):
        self.original_activities = deepcopy(activities)
        self.client = TestClient(app)

    def tearDown(self):
        activities.clear()
        activities.update(self.original_activities)
        self.client.close()

    def test_unregister_removes_only_selected_participant_and_allows_signup(self):
        email = activities["Chess Club"]["participants"][0]
        others = activities["Chess Club"]["participants"][1:]

        response = self.client.delete(
            "/activities/Chess%20Club/unregister", params={"email": email}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"message": f"Unregistered {email} from Chess Club"}
        )
        updated = self.client.get("/activities").json()
        self.assertEqual(updated["Chess Club"]["participants"], others)
        self.assertEqual(
            updated["Programming Class"], self.original_activities["Programming Class"]
        )
        signup = self.client.post(
            "/activities/Chess%20Club/signup", params={"email": email}
        )
        self.assertEqual(signup.status_code, 200)

    def test_unregister_last_participant_leaves_empty_list(self):
        email = "student+club@example.com"
        activities["Art Club"]["participants"] = [email]

        response = self.client.delete(
            "/activities/Art%20Club/unregister", params={"email": email}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.get("/activities").json()["Art Club"]["participants"], []
        )

    def test_missing_activity_or_participant_returns_error_without_changes(self):
        for activity, detail in [
            ("Unknown", "Activity not found"),
            ("Chess Club", "Participant not found"),
        ]:
            with self.subTest(activity=activity):
                response = self.client.delete(
                    f"/activities/{activity}/unregister",
                    params={"email": "missing@example.com"},
                )
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json(), {"detail": detail})
                self.assertEqual(activities, self.original_activities)
