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
load_dotenv(dotenv_path=env_path)

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


def generate_otp_code(length: int = 6) -> str:
    """Generates a secure 6-digit numeric OTP code."""
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def send_verification_otp_email(
    to_email: str,
    otp_code: str,
    purpose: str = "reset_password",
    reset_url: str = None,
) -> tuple[bool, str]:
    """
    Sends an official 6-digit OTP verification email to the user's Gmail/work email via SMTP.
    Supports both Gmail and custom SMTP servers with TLS/SSL.
    Returns (success: bool, status_message: str).
    """
    smtp_host = os.getenv("SMTP_HOST") or os.getenv("EMAIL_HOST")
    smtp_port_raw = os.getenv("SMTP_PORT") or os.getenv("EMAIL_PORT") or "587"
    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        logger.error("SMTP_PORT must be a valid port number.")
        return False, "Email delivery is not configured correctly."

    if not 1 <= smtp_port <= 65535:
        logger.error("SMTP_PORT must be between 1 and 65535.")
        return False, "Email delivery is not configured correctly."

    smtp_user = os.getenv("SMTP_USER") or os.getenv("EMAIL_HOST_USER")
    smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("EMAIL_HOST_PASSWORD")

    use_ssl = (
        smtp_port == 465 or
        str(os.getenv("SMTP_SSL") or os.getenv("EMAIL_USE_SSL", "False")).lower() in ("true", "1", "yes")
    )
    use_tls = str(os.getenv("SMTP_TLS") or os.getenv("EMAIL_USE_TLS", "True")).lower() in ("true", "1", "yes")

    from_email = os.getenv("FROM_EMAIL") or os.getenv("DEFAULT_FROM_EMAIL") or smtp_user or "support@hrtechadvisor.local"

    is_login = purpose == "login"
    subject = f"HR-Tech Advisor — Your Login OTP: {otp_code}" if is_login else f"HR-Tech Advisor — Password Reset OTP: {otp_code}"
    headline = "Your Login Verification OTP" if is_login else "Reset Your Password"
    action_desc = "Enter this One-Time Password to securely sign in to your HR-Tech Advisor founder portal:" if is_login else "We received a request to reset your HR-Tech Advisor password. Use the 6-digit OTP below to set a new password:"

    if not smtp_host or not smtp_user or not smtp_password:
        logger.error("SMTP email settings are missing; verification email was not sent.")
        return False, "Email delivery is not configured."

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"HR-Tech Advisor <{from_email}>"
        msg["To"] = to_email

        text_content = (
            f"Hello,\n\n"
            f"{action_desc}\n\n"
            f"VERIFICATION OTP: {otp_code}\n\n"
            f"This code will expire in 15 minutes. Do not share this OTP with anyone.\n"
        )
        if reset_url and not is_login:
            text_content += f"\nOr directly reset using this link:\n{reset_url}\n"
        text_content += "\nBest regards,\nThe HR-Tech Advisor Team\n"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; margin: 0; padding: 32px 16px; color: #f8fafc; }}
            .container {{ max-width: 520px; margin: 0 auto; background: rgba(30, 41, 59, 0.85); border-radius: 16px; padding: 36px; border: 1px solid rgba(255, 255, 255, 0.12); box-shadow: 0 20px 40px -15px rgba(0,0,0,0.5); backdrop-filter: blur(12px); }}
            .brand {{ font-size: 20px; font-weight: 700; color: #818cf8; margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }}
            .title {{ font-size: 22px; font-weight: 700; color: #ffffff; margin-bottom: 12px; }}
            .text {{ font-size: 15px; color: #cbd5e1; line-height: 1.6; margin-bottom: 24px; }}
            .otp-box {{ background: rgba(79, 70, 229, 0.15); border: 1.5px solid rgba(129, 140, 248, 0.4); border-radius: 12px; padding: 20px; text-align: center; margin: 24px 0; }}
            .otp-code {{ font-family: 'SFMono-Regular', Consolas, Monaco, monospace; font-size: 34px; font-weight: 800; letter-spacing: 10px; color: #ffffff; margin: 0; }}
            .otp-sub {{ font-size: 13px; color: #94a3b8; margin-top: 8px; }}
            .btn {{ display: inline-block; background-color: #4f46e5; color: #ffffff !important; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 16px; }}
            .footer {{ font-size: 13px; color: #64748b; margin-top: 32px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 16px; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="brand">HR-Tech Advisor</div>
            <div class="title">{headline}</div>
            <div class="text">{action_desc}</div>
            <div class="otp-box">
              <div class="otp-code">{otp_code}</div>
              <div class="otp-sub">Valid for 15 minutes &bull; Do not share with anyone</div>
            </div>

            {f'<p class="text" style="font-size: 14px; margin-top: 20px;">Or click below to open the reset form:<br><a href="{reset_url}" class="btn" target="_blank">Reset Password &rarr;</a></p>' if (reset_url and not is_login) else ''}

            <div class="footer">
              &copy; HR-Tech Advisor. Digital HR Maturity Diagnostics & Tool Matching.
            </div>
          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        if use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=12) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
                if use_tls:
                    server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

        logger.info("Sent verification email via SMTP (purpose: %s).", purpose)
        return True, f"A 6-digit verification code has been sent to your Gmail ({to_email})."
    except (OSError, smtplib.SMTPException):
        logger.exception("Could not send verification email via SMTP.")
        return False, "Email delivery failed. Check SMTP configuration and connectivity."


def send_password_reset_email(to_email: str, reset_url: str, otp_code: str = None) -> tuple[bool, str]:
    """
    Backward-compatible wrapper for sending password reset emails with OTP.
    """
    if not otp_code:
        otp_code = generate_otp_code()
    return send_verification_otp_email(
        to_email=to_email,
        otp_code=otp_code,
        purpose="reset_password",
        reset_url=reset_url,
    )
