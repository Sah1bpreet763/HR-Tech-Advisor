"""
MODULE 2 API — Registration & Login.

The Django frontend calls these endpoints server-side (not from browser
JS), so no CORS or token scheme is needed for the MVP: Django keeps the
logged-in state in its own session after getting user_id/startup_id back.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database import models
from datetime import datetime, timedelta
from backend.schemas.auth import (
    RegisterRequest, LoginRequest, AuthResponse,
    ForgotPasswordRequest, ForgotPasswordResponse,
    VerifyTokenResponse, ResetPasswordRequest,
)
from backend.services.auth_service import (
    hash_password, verify_password,
    generate_reset_token, send_password_reset_email,
)

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")

    user = models.User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.flush()

    startup = models.Startup(
        user_id=user.id,
        company_name=payload.company_name,
        industry=payload.industry,
        team_size=payload.team_size,
        growth_stage=payload.growth_stage,
        hr_budget_monthly=payload.hr_budget_monthly,
        location=payload.location,
        contact_email=payload.contact_email or payload.email,
    )
    db.add(startup)
    db.commit()
    db.refresh(startup)

    return AuthResponse(user_id=user.id, startup_id=startup.id, company_name=startup.company_name)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    startup = db.query(models.Startup).filter(models.Startup.user_id == user.id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="No startup profile found for this account")

    return AuthResponse(user_id=user.id, startup_id=startup.id, company_name=startup.company_name)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiates the password reset flow.
    Generates a secure 1-hour token, stores it in DB, and dispatches via SMTP.
    If SMTP is not configured, provides a direct test link to prevent blocking local development.
    """
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        # Returning generic message prevents email enumeration
        return ForgotPasswordResponse(
            message="If an account with that email exists, we have sent instructions to reset your password.",
            reset_url=None,
            email_sent=False,
        )

    # Invalidate previous unexpired tokens
    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user.id,
        models.PasswordResetToken.is_used == False,
    ).update({"is_used": True})

    token = generate_reset_token()
    expires_at = datetime.utcnow() + timedelta(hours=1)
    reset_entry = models.PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
        is_used=False,
    )
    db.add(reset_entry)
    db.commit()

    reset_url = f"http://127.0.0.1:8080/accounts/reset-password/?token={token}"
    email_sent, status_detail = send_password_reset_email(user.email, reset_url)

    return ForgotPasswordResponse(
        message="If an account with that email exists, we have sent instructions to reset your password.",
        reset_url=reset_url if not email_sent else None,
        email_sent=email_sent,
        status_detail=status_detail,
    )


@router.get("/verify-reset-token", response_model=VerifyTokenResponse)
def verify_reset_token(token: str, db: Session = Depends(get_db)):
    """Verifies whether a password reset token is valid and unexpired."""
    record = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == token
    ).first()

    if not record:
        return VerifyTokenResponse(valid=False, detail="Reset token not found.")
    if record.is_used:
        return VerifyTokenResponse(valid=False, detail="This reset token has already been used.")
    if record.expires_at < datetime.utcnow():
        return VerifyTokenResponse(valid=False, detail="This reset token has expired. Please request a new one.")

    return VerifyTokenResponse(valid=True, email=record.user.email)


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Resets the password using a valid reset token."""
    record = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == payload.token
    ).first()

    if not record or record.is_used or record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    user = record.user
    user.hashed_password = hash_password(payload.new_password)
    record.is_used = True
    db.commit()

    return {"message": "Password has been successfully updated. You may now log in."}

