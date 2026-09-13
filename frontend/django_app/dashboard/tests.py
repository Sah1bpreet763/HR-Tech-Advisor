from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch


class DashboardFrontendTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_unauthenticated_dashboard_redirects_to_login(self):
        resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp.url)

    @patch("requests.get")
    def test_authenticated_dashboard_renders(self, mock_get):
        # Mock profile and history calls
        def side_effect(url, **kwargs):
            class MockResponse:
                def __init__(self, status_code, json_data):
                    self.status_code = status_code
                    self._json = json_data
                def json(self):
                    return self._json

            if "/api/startups/" in url:
                return MockResponse(200, {
                    "id": 1,
                    "company_name": "TestCorp",
                    "industry": "Fintech",
                    "team_size": 35,
                    "hr_budget_monthly": 10000.0,
                    "location": "Delhi",
                })
            elif "/api/audit/history/" in url:
                return MockResponse(200, [])
            return MockResponse(404, {})

        mock_get.side_effect = side_effect

        session = self.client.session
        session["user_id"] = 1
        session["startup_id"] = 1
        session["company_name"] = "TestCorp"
        session.save()

        resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "TestCorp")
        self.assertContains(resp, "35 employees")
        self.assertContains(resp, "₹10000.0")

    @patch("requests.get")
    def test_authenticated_questionnaire_renders(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {
                "id": 1,
                "text": "How do you track attendance?",
                "category_id": 1,
                "category_name": "Attendance",
                "options": [
                    {"id": 101, "label": "Manual Register"},
                    {"id": 102, "label": "Biometric System"},
                ],
            }
        ]

        session = self.client.session
        session["user_id"] = 1
        session["startup_id"] = 1
        session["company_name"] = "TestCorp"
        session.save()

        resp = self.client.get(reverse("dashboard:questionnaire"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Digital HR Maturity Audit")
        self.assertContains(resp, "How do you track attendance?")
        self.assertContains(resp, "Biometric System")

