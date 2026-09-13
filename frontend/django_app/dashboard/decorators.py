"""
Simple session-based login check.

We don't use Django's built-in @login_required because Django doesn't
own the User model here — being "logged in" just means the session has
a user_id/startup_id that FastAPI's /api/auth/login or /register gave us.
"""
from functools import wraps
from django.shortcuts import redirect


def session_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("accounts:login")
        return view_func(request, *args, **kwargs)
    return wrapper
