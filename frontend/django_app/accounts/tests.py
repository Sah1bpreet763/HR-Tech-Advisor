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

    @patch("requests.post")
    def test_forgot_password_submission(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "message": "Instructions sent",
            "reset_url": "http://127.0.0.1:8080/accounts/reset-password/?token=abc123xyz",
            "email_sent": False,
        }
        resp = self.client.post(reverse("accounts:forgot_password"), {"email": "test@startup.io"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Reset Instructions Sent")
        self.assertContains(resp, "token=abc123xyz")

    @patch("requests.post")
    def test_forgot_password_email_sent_alert(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "message": "Instructions sent",
            "reset_url": None,
            "email_sent": True,
            "status_detail": "Password reset instructions have been sent.",
        }
        resp = self.client.post(reverse("accounts:forgot_password"), {"email": "test@startup.io"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Reset Instructions Sent")

