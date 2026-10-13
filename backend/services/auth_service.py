"""
MODULE 2 — Password hashing helpers & Email Authentication Service.

Uses Python's built-in hashlib (PBKDF2-HMAC-SHA256) so no extra native
dependency (like bcrypt) is required for the MVP. Good enough for a
student/prototype project; a production deployment should move to
bcrypt or argon2 via passlib.
"""
import hashlib
import hmac
import logging
import os
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded from root directory
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

logger = logging.getLogger("auth_service")

PBKDF2_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$")
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return hmac.compare_digest(dk.hex(), hash_hex)


def generate_reset_token() -> str:
    """Generates a cryptographically strong, URL-safe reset token."""
    return secrets.token_urlsafe(32)


def send_password_reset_email(to_email: str, reset_url: str) -> tuple[bool, str]:
    """
    Sends an official password reset email via SMTP if credentials are set in .env.
    Supports both SMTP_* and EMAIL_* conventions, SSL (port 465) and TLS (port 587).
    Returns (success: bool, status_message: str).
    """
    # Reload environment to catch runtime changes in .env
    load_dotenv(dotenv_path=env_path, override=True)

    smtp_host = os.getenv("SMTP_HOST") or os.getenv("EMAIL_HOST")
    smtp_port_raw = os.getenv("SMTP_PORT") or os.getenv("EMAIL_PORT") or "587"
    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        smtp_port = 587

    smtp_user = os.getenv("SMTP_USER") or os.getenv("EMAIL_HOST_USER")
    smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("EMAIL_HOST_PASSWORD")
    
    use_ssl = (
        smtp_port == 465 or
        str(os.getenv("SMTP_SSL") or os.getenv("EMAIL_USE_SSL", "False")).lower() in ("true", "1", "yes")
    )
    use_tls = str(os.getenv("SMTP_TLS") or os.getenv("EMAIL_USE_TLS", "True")).lower() in ("true", "1", "yes")
    
    from_email = os.getenv("FROM_EMAIL") or os.getenv("DEFAULT_FROM_EMAIL") or smtp_user or "support@hrtechadvisor.local"

    if not smtp_host or not smtp_user or not smtp_password:
        msg = (
            "Live email delivery requires SMTP credentials in your .env file "
            "(e.g. SMTP_HOST=smtp.gmail.com, SMTP_PORT=587, SMTP_USER=your-email@gmail.com, "
            "SMTP_PASSWORD=your-app-password)."
        )
        logger.info(
            f"[SMTP NOT CONFIGURED] Password reset requested for {to_email}. "
            f"Reset Link: {reset_url}"
        )
        return False, msg

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "HR-Tech Advisor — Password Reset Request"
        msg["From"] = f"HR-Tech Advisor <{from_email}>"
        msg["To"] = to_email

        text_content = (
            f"Hello,\n\n"
            f"We received a request to reset your HR-Tech Advisor account password.\n"
            f"Click the link below to set a new password:\n\n"
            f"{reset_url}\n\n"
            f"This link is valid for 1 hour. If you did not request this, please ignore this email.\n\n"
            f"Best regards,\n"
            f"The HR-Tech Advisor Team"
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
            .container {{ max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 32px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
            .brand {{ font-size: 20px; font-weight: bold; color: #4f46e5; margin-bottom: 24px; }}
            .btn {{ display: inline-block; background-color: #4f46e5; color: #ffffff !important; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 20px 0; }}
            .footer {{ font-size: 13px; color: #64748b; margin-top: 32px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="brand">HR-Tech Advisor</div>
            <h2>Reset Your Password</h2>
            <p>We received a request to reset your HR-Tech Advisor password. Click the button below to choose a new password:</p>
            <p><a href="{reset_url}" class="btn" target="_blank">Reset Password</a></p>
            <p style="font-size: 14px; color: #64748b;">Or copy and paste this URL into your browser:<br><a href="{reset_url}">{reset_url}</a></p>
            <p style="font-size: 14px; color: #94a3b8;">This link will expire in 60 minutes. If you did not request a password reset, you can safely ignore this email.</p>
            <div class="footer">
              &copy; HR-Tech Advisor. All rights reserved.
            </div>
          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=12)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=12)
            if use_tls:
                server.starttls()

        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        logger.info(f"Successfully sent password reset email to {to_email} via SMTP.")
        return True, f"Password reset instructions have been sent to {to_email}."
    except Exception as exc:
        err_msg = f"SMTP connection error: {exc}"
        logger.error(f"Failed to send reset email to {to_email} via SMTP: {err_msg}")
        return False, err_msg


