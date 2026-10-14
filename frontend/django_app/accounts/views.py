import requests
import logging

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, StartupProfileForm
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
    if request.session.get("user_id"):
        return redirect("dashboard:home")

    if request.method == "POST":
        form = LoginForm(request.POST)

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
                    logger.error(
                        "Login API returned non-JSON response. Status: %s",
                        resp.status_code,
                    )
                    logger.error("Login API response body: %s", resp.text[:1000])
                    form.add_error(
                        None,
                        "The login service returned an unexpected response. "
                        "Please try again later.",
                    )
                else:
                    if resp.status_code == 200:
                        request.session["user_id"] = result["user_id"]
                        request.session["startup_id"] = result["startup_id"]
                        request.session["company_name"] = result["company_name"]

                        return redirect("dashboard:home")

                    form.add_error(None, "Invalid email or password.")

            except requests.RequestException:
                logger.exception("FastAPI login request failed")
                form.add_error(
                    None,
                    "Could not reach the login service. Please try again later.",
                )

            except (KeyError, TypeError):
                logger.exception(
                    "Unexpected login API response structure"
                )
                form.add_error(
                    None,
                    "The login service returned unexpected data. "
                    "Please try again later.",
                )
            except Exception:
                logger.exception("Unexpected error in login_view")
                form.add_error(
                    None,
                    "An unexpected error occurred. Please try again.",
                )

    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    request.session.flush()
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


def forgot_password_view(request):
    """
    Handles forgot-password requests.
    Supports real SMTP email delivery as well as an interactive dev-mode preview
    if SMTP credentials are not yet configured in .env.
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
                    timeout=5,
                )
            except requests.RequestException:
                form.add_error(None, "Could not reach the HR-Tech Advisor backend. Is it running?")
            else:
                if resp.status_code == 200:
                    reset_info = resp.json()
                    messages.success(request, f"Password reset instructions have been processed for {email}.")
                else:
                    form.add_error(None, "Unable to process password reset request.")
    else:
        form = ForgotPasswordForm()

    return render(request, "accounts/forgot_password.html", {"form": form, "reset_info": reset_info})


def reset_password_view(request):
    """
    Validates token and handles new password submission.
    """
    token = request.GET.get("token") or request.POST.get("token")
    if not token:
        messages.error(request, "Password reset token is missing. Please request a new link.")
        return redirect("accounts:forgot_password")

    # Verify token validity against backend
    try:
        verify_resp = requests.get(
            f"{settings.FASTAPI_BASE_URL}/api/auth/verify-reset-token",
            params={"token": token},
            timeout=5,
        )
    except requests.RequestException:
        messages.error(request, "Could not reach backend service to verify token.")
        return redirect("accounts:login")

    token_data = verify_resp.json()
    if not token_data.get("valid"):
        detail = token_data.get("detail", "This password reset link is invalid or has expired.")
        return render(request, "accounts/reset_password.html", {"token_invalid": True, "detail": detail})

    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password"]
            try:
                resp = requests.post(
                    f"{settings.FASTAPI_BASE_URL}/api/auth/reset-password",
                    json={"token": token, "new_password": new_password},
                    timeout=5,
                )
            except requests.RequestException:
                form.add_error(None, "Could not reach backend service.")
            else:
                if resp.status_code == 200:
                    messages.success(request, "Your password has been reset successfully. You can now log in.")
                    return redirect("accounts:login")
                else:
                    detail = resp.json().get("detail", "Password reset failed.")
                    form.add_error(None, detail)
    else:
        form = ResetPasswordForm()

    return render(request, "accounts/reset_password.html", {
        "form": form,
        "token": token,
        "email": token_data.get("email"),
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

