from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch


class DashboardFrontendTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_landing_page_shows_hr_features_only(self):
        resp = self.client.get(reverse("landing"))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "HR Audits &amp; Maturity Scoring")
        self.assertContains(resp, "Performance &amp; Engagement")
        self.assertContains(resp, "HR Tool Recommendations")
        self.assertNotContains(resp, "Product Design")
        self.assertNotContains(resp, "UX/UI Design")
        self.assertNotContains(resp, "Education")
        for module_number in range(1, 4):
            self.assertNotContains(resp, f"Module {module_number}")

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
        self.assertContains(resp, "Attendance Management")
        self.assertContains(resp, "Performance Management")
        self.assertNotContains(resp, "Attendance Automation")
        self.assertNotContains(resp, "Performance &amp; OKRs")

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
        self.assertNotContains(resp, "Module 3")
