import unittest
from unittest.mock import patch

from web_app import app


class AstraAPITests(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.base_url = "http://127.0.0.1:5000"

    def get(self, path):
        return self.client.get(
            path,
            base_url=self.base_url
        )

    def test_health(self):
        response = self.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "online")

    def test_student_dashboard(self):
        response = self.get("/api/student/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn("subjects", response.json)
        self.assertIn("stats", response.json)

    def test_exams(self):
        response = self.get("/api/student/exams")
        self.assertEqual(response.status_code, 200)

    def test_reminders(self):
        response = self.get("/api/student/reminders")
        self.assertEqual(response.status_code, 200)

    def test_system_status(self):
        response = self.get("/api/system/status")
        self.assertEqual(response.status_code, 200)
        self.assertIn("cpu", response.json)
        self.assertIn("ram", response.json)

    def test_memory(self):
        response = self.get("/api/memory")
        self.assertEqual(response.status_code, 200)

    def test_study_planner(self):
        response = self.get("/api/study/sessions")
        self.assertEqual(response.status_code, 200)

    def test_quiz_analytics(self):
        response = self.get("/api/quiz/analytics")
        self.assertEqual(response.status_code, 200)

    def test_empty_chat(self):
        response = self.client.post(
            "/api/chat",
            json={"message": ""},
            base_url=self.base_url
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_vision_question(self):
        response = self.client.post(
            "/api/vision/analyze",
            json={"question": ""},
            base_url=self.base_url
        )
        self.assertEqual(response.status_code, 400)

    @patch("web_app.analyze_screen")
    def test_vision_permission_denied(self, vision):

        vision.return_value = {
            "success": False,
            "status": "error",
            "error_code": "PERMISSION_DENIED",
            "message": "Permission denied."
        }

        response = self.client.post(
            "/api/vision/analyze",
            json={"question": "Explain my screen"},
            base_url=self.base_url
        )

        self.assertEqual(response.status_code, 403)

    @patch("web_app.analyze_screen")
    def test_vision_success(self, vision):

        vision.return_value = {
            "success": True,
            "status": "success",
            "data": {
                "analysis": "Simulated screen analysis."
            }
        }

        response = self.client.post(
            "/api/vision/analyze",
            json={"question": "Explain my screen"},
            base_url=self.base_url
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json["response"],
            "Simulated screen analysis."
        )

    def test_remote_access_blocked(self):
        response = self.client.get(
            "/api/health",
            base_url=self.base_url,
            environ_overrides={
                "REMOTE_ADDR": "192.168.1.100"
            }
        )
        self.assertEqual(response.status_code, 403)

    def test_invalid_host_blocked(self):
        response = self.client.get(
            "/api/health",
            base_url="http://untrusted.example:5000"
        )
        self.assertEqual(response.status_code, 403)

    def test_cross_origin_blocked(self):
        response = self.client.post(
            "/api/chat",
            json={"message": "Test"},
            base_url=self.base_url,
            headers={
                "Origin": "https://untrusted.example"
            }
        )
        self.assertEqual(response.status_code, 403)

    def test_security_headers(self):
        response = self.get("/api/health")
        self.assertEqual(
            response.headers["X-Frame-Options"],
            "DENY"
        )
        self.assertEqual(
            response.headers["X-Content-Type-Options"],
            "nosniff"
        )

    def test_api_cache_protection(self):
        response = self.get("/api/health")
        self.assertEqual(
            response.headers["Cache-Control"],
            "no-store"
        )


if __name__ == "__main__":
    unittest.main()
