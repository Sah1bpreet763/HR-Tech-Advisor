import requests
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import (
    RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, StartupProfileForm,
    LoginOTPRequestForm, LoginOTPVerifyForm,
)
from dashboard.decorators import session_login_required


logger = logging.getLogger(__name__)



def register_view(request):
    if request.session.get("user_id"):
        return redirect("dashboard:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            payload = {
                "email": data["email"],
                "password": data["password"],
                "company_name": data["company_name"],
                "industry": data.get("industry") or None,
                "team_size": data.get("team_size"),
                "growth_stage": data.get("growth_stage") or None,
                "hr_budget_monthly": data.get("hr_budget_monthly"),
                "location": data.get("location") or None,
            }

            try:
                resp = requests.post(
                    f"{settings.FASTAPI_BASE_URL.rstrip('/')}/api/auth/register",
                    json=payload,
                    timeout=20,
                )

                try:
                    result = resp.json()
                except ValueError:
                    logger.error(
                        "Registration API returned non-JSON response. "
                        "Status code: %s",
                        resp.status_code,
                    )
                    form.add_error(
                        None,
                        "The registration service returned an unexpected response. "
                        "Please try again later.",
                    )
                else:
                    if resp.status_code == 200:
                        request.session["user_id"] = result["user_id"]
                        request.session["startup_id"] = result["startup_id"]
                        request.session["company_name"] = result["company_name"]

                        messages.success(
                            request,
                            f"Welcome, {result['company_name']}! "
                            "Your account is ready.",
                        )
                        return redirect("dashboard:home")

                    detail = result.get(
                        "detail",
                        "Registration failed. Please check your details.",
                    )

                    if isinstance(detail, (dict, list)):
                        detail = "Registration failed. Please check your details."

                    form.add_error(None, str(detail))

            except requests.RequestException:
                logger.exception("FastAPI registration request failed")
                form.add_error(
                    None,
                    "Could not reach the registration service. "
                    "Please try again later.",
                )

            except (KeyError, TypeError):
                logger.exception(
                    "Unexpected registration API response structure"
                )
                form.add_error(
                    None,
                    "The registration service returned unexpected data. "
                    "Please try again later.",
                )

    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )



def login_view(request):
    """
    Supports both standard Password Authentication and Gmail OTP Verification for login.
    """
    if request.session.get("user_id"):
        return redirect("dashboard:home")

    form = LoginForm()
    otp_request_form = LoginOTPRequestForm()
    otp_verify_form = LoginOTPVerifyForm()
    active_tab = "password"
    otp_sent_to = None

    if request.method == "POST":
        action = request.POST.get("auth_action", "password")

        # 1. Standard Password Sign In
        if action == "password":
            form = LoginForm(request.POST)
            active_tab = "password"
            if form.is_valid():
                data = form.cleaned_data
                try:
                    resp = requests.post(
                        f"{settings.FASTAPI_BASE_URL.rstrip('/')}/api/auth/login",
                        json={
                            "email": data["email"],
                            "password": data["password"],
                        },
                        timeout=20,
                    )
                    try:
                        result = resp.json()
                    except ValueError:
                        form.add_error(None, "The login service returned an unexpected response.")
                    else:
                        if resp.status_code == 200:
                            request.session["user_id"] = result["user_id"]
                            request.session["startup_id"] = result["startup_id"]
                            request.session["company_name"] = result["company_name"]
                            messages.success(request, f"Welcome back, {result['company_name']}!")
                            return redirect("dashboard:home")
                        form.add_error(None, "Invalid email or password.")
                except requests.RequestException:
                    form.add_error(None, "Could not reach the login service. Please ensure the backend is running.")

        # 2. Request OTP to Gmail for Sign In
        elif action == "request_otp":
            otp_request_form = LoginOTPRequestForm(request.POST)
            active_tab = "otp"
            if otp_request_form.is_valid():
                email = otp_request_form.cleaned_data["email"]
                try:
                    resp = requests.post(
                        f"{settings.FASTAPI_BASE_URL.rstrip('/')}/api/auth/send-login-otp",
                        json={"email": email},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        otp_sent_to = email
                        otp_verify_form = LoginOTPVerifyForm(initial={"email": email})
                        messages.success(request, f"A 6-digit login OTP has been sent to your Gmail ({email}).")
                    else:
                        otp_request_form.add_error(None, "Unable to generate login OTP. Please check your email.")
                except requests.RequestException:
                    otp_request_form.add_error(None, "Could not reach backend service.")

        # 3. Verify OTP from Gmail and Complete Sign In
        elif action == "verify_otp":
            otp_verify_form = LoginOTPVerifyForm(request.POST)
            active_tab = "otp"
            if otp_verify_form.is_valid():
                email = otp_verify_form.cleaned_data["email"]
                otp_code = otp_verify_form.cleaned_data["otp_code"]
                try:
                    resp = requests.post(
                        f"{settings.FASTAPI_BASE_URL.rstrip('/')}/api/auth/verify-login-otp",
                        json={"email": email, "otp_code": otp_code},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        request.session["user_id"] = result["user_id"]
                        request.session["startup_id"] = result["startup_id"]
                        request.session["company_name"] = result["company_name"]
                        messages.success(request, f"Verified with Gmail OTP! Welcome back, {result['company_name']}.")
                        return redirect("dashboard:home")
                    else:
                        detail = resp.json().get("detail", "Invalid OTP code.")
                        otp_verify_form.add_error("otp_code", detail)
                        otp_sent_to = email
                except requests.RequestException:
                    otp_verify_form.add_error(None, "Could not reach login service.")
                    otp_sent_to = email

    return render(request, "accounts/login.html", {
        "form": form,
        "otp_request_form": otp_request_form,
        "otp_verify_form": otp_verify_form,
        "active_tab": active_tab,
        "otp_sent_to": otp_sent_to,
    })


def logout_view(request):
    request.session.flush()
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


def forgot_password_view(request):
    """
    Handles forgot-password requests:
    Generates a 6-digit OTP code and dispatches it directly to the user's Gmail.
    Shows the confirmation card with direct navigation to enter the Gmail OTP and reset password.
    """
    if request.session.get("user_id"):
        return redirect("dashboard:home")

    reset_info = None
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                resp = requests.post(
                    f"{settings.FASTAPI_BASE_URL}/api/auth/forgot-password",
                    json={"email": email},
                    timeout=10,
                )
            except requests.RequestException:
                form.add_error(None, "Could not reach the HR-Tech Advisor backend. Is it running?")
            else:
                if resp.status_code == 200:
                    reset_url = reverse("accounts:reset_password")
                    reset_info = {
                        "reset_url": request.build_absolute_uri(
                            f"{reset_url}?{urlencode({'email': email})}"
                        )
                    }

                    messages.success(
                        request,
                        "If an account exists for that email, a verification code has been sent."
                    )
                else:
                    form.add_error(
                        None,
                        "Unable to send a verification code. Please check the email settings or try again later.",
                    )
    else:
        form = ForgotPasswordForm()

    return render(request, "accounts/forgot_password.html", {"form": form, "reset_info": reset_info})


def reset_password_view(request):
    """
    Validates the 6-digit OTP received in Gmail (or token) and updates the password.
    """
    token = request.GET.get("token") or request.POST.get("token") or ""
    email = request.GET.get("email") or request.POST.get("email") or ""

    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password"]
            otp_code = form.cleaned_data.get("otp_code") or request.POST.get("otp_code", "").strip()
            submit_email = form.cleaned_data.get("email") or email

            payload = {
                "token": token or None,
                "email": submit_email or None,
                "otp_code": otp_code or None,
                "new_password": new_password,
            }

            try:
                resp = requests.post(
                    f"{settings.FASTAPI_BASE_URL}/api/auth/reset-password",
                    json=payload,
                    timeout=10,
                )
            except requests.RequestException:
                form.add_error(None, "Could not reach backend service to reset password.")
            else:
                if resp.status_code == 200:
                    messages.success(request, "Your password has been successfully reset! You can now sign in.")
                    return redirect("accounts:login")
                else:
                    detail = resp.json().get("detail", "Password reset failed. Please check your OTP code.")
                    form.add_error(None, detail)
    else:
        initial_data = {}
        if email:
            initial_data["email"] = email
        form = ResetPasswordForm(initial=initial_data)

    return render(request, "accounts/reset_password.html", {
        "form": form,
        "token": token,
        "email": email,
    })


@session_login_required
def profile_view(request):
    """
    Allows founders to update their startup parameters (team size, HR budget, industry, etc.).
    """
    startup_id = request.session["startup_id"]
    startup = None
    try:
        resp = requests.get(f"{settings.FASTAPI_BASE_URL}/api/startups/{startup_id}", timeout=5)
        if resp.status_code == 200:
            startup = resp.json()
    except requests.RequestException:
        messages.error(request, "Could not load startup profile.")

    if request.method == "POST":
        form = StartupProfileForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            payload = {
                "company_name": data["company_name"],
                "industry": data.get("industry") or None,
                "team_size": data.get("team_size"),
                "growth_stage": data.get("growth_stage") or None,
                "hr_budget_monthly": data.get("hr_budget_monthly"),
                "location": data.get("location") or None,
                "contact_email": data.get("contact_email") or None,
            }
            try:
                up_resp = requests.put(
                    f"{settings.FASTAPI_BASE_URL}/api/startups/{startup_id}",
                    json=payload,
                    timeout=5,
                )
                if up_resp.status_code == 200:
                    updated = up_resp.json()
                    request.session["company_name"] = updated["company_name"]
                    messages.success(request, "Startup profile updated successfully.")
                    return redirect("accounts:profile")
                else:
                    form.add_error(None, "Failed to update profile.")
            except requests.RequestException:
                form.add_error(None, "Could not reach backend to save profile changes.")
    else:
        initial_data = {
            "company_name": startup.get("company_name", "") if startup else "",
            "industry": startup.get("industry", "") if startup else "",
            "team_size": startup.get("team_size") if startup else None,
            "growth_stage": startup.get("growth_stage", "") if startup else "",
            "hr_budget_monthly": startup.get("hr_budget_monthly") if startup else None,
            "location": startup.get("location", "") if startup else "",
            "contact_email": startup.get("contact_email", "") if startup else "",
        }
        form = StartupProfileForm(initial=initial_data)

    return render(request, "accounts/profile.html", {"form": form, "startup": startup})
