from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch


class AccountsFrontendTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_page_renders_with_forgot_password(self):
        resp = self.client.get(reverse("accounts:login"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Forgot password?")
        self.assertContains(resp, reverse("accounts:forgot_password"))

    def test_register_page_renders(self):
        resp = self.client.get(reverse("accounts:register"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Create Founder Account")

    def test_forgot_password_page_renders(self):
        resp = self.client.get(reverse("accounts:forgot_password"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Forgot Password?")

    @patch("accounts.views.requests.post")
    def test_login_otp_request_does_not_display_code(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"otp_code": "987654"}

        resp = self.client.post(
            reverse("accounts:login"),
            {"auth_action": "request_otp", "email": "test@startup.io"},
        )

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "OTP Dispatched!")
        self.assertNotContains(resp, "987654")

    @patch("accounts.views.requests.post")
    def test_login_otp_verification_logs_user_in(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "user_id": 7,
            "startup_id": 11,
            "company_name": "Test Startup",
        }

        resp = self.client.post(
            reverse("accounts:login"),
            {
                "auth_action": "verify_otp",
                "email": "test@startup.io",
                "otp_code": "123456",
            },
        )

        self.assertRedirects(
            resp,
            reverse("dashboard:home"),
            fetch_redirect_response=False,
        )
        self.assertEqual(self.client.session["user_id"], 7)
        self.assertEqual(self.client.session["startup_id"], 11)

    @patch("requests.post")
    def test_forgot_password_submission(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "message": "Instructions sent",
        }
        resp = self.client.post(reverse("accounts:forgot_password"), {"email": "test@startup.io"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Reset Instructions Sent")
        self.assertContains(resp, "reset-password/?email=test%40startup.io")
        self.assertNotContains(resp, "Development Mode OTP")

    @patch("requests.post")
    def test_forgot_password_email_sent_alert(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "message": "Instructions sent",
        }
        resp = self.client.post(reverse("accounts:forgot_password"), {"email": "test@startup.io"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Reset Instructions Sent")
        self.assertNotContains(resp, "otp_code")
