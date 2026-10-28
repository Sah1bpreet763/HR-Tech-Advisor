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
    VerifyOTPRequest, VerifyOTPResponse,
    ResetPasswordOTPRequest, SendLoginOTPRequest, VerifyLoginOTPRequest,
)
from backend.services.auth_service import (
    hash_password, verify_password,
    generate_reset_token, generate_otp_code,
    send_verification_otp_email,
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
    Generates a secure 6-digit OTP and reset token, stores them in DB, and dispatches
    the OTP to the user's Gmail/work email via SMTP.
    """
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        # Returning generic message prevents email enumeration
        return ForgotPasswordResponse(
            message="If an account with that email exists, we have sent instructions and an OTP to reset your password.",
        )

    # Invalidate previous unexpired reset tokens and OTPs
    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user.id,
        models.PasswordResetToken.is_used == False,
    ).update({"is_used": True})

    db.query(models.EmailOTP).filter(
        models.EmailOTP.user_id == user.id,
        models.EmailOTP.purpose == "reset_password",
        models.EmailOTP.is_used == False,
    ).update({"is_used": True})

    token = generate_reset_token()
    otp_code = generate_otp_code()
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    reset_entry = models.PasswordResetToken(
        user_id=user.id,
        token=token,
        otp_code=otp_code,
        expires_at=expires_at,
        is_used=False,
    )
    email_otp = models.EmailOTP(
        user_id=user.id,
        email=user.email,
        otp_code=otp_code,
        purpose="reset_password",
        expires_at=expires_at,
        is_used=False,
    )
    db.add(reset_entry)
    db.add(email_otp)
    db.commit()

    email_sent, _ = send_verification_otp_email(
        to_email=user.email,
        otp_code=otp_code,
        purpose="reset_password",
    )
    if not email_sent:
        reset_entry.is_used = True
        email_otp.is_used = True
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Could not send the verification email. Please try again later.",
        )

    return ForgotPasswordResponse(
        message="If an account with that email exists, we have sent instructions and a 6-digit OTP to your Gmail to reset your password.",
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


@router.post("/verify-otp", response_model=VerifyOTPResponse)
def verify_otp(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verifies whether a 6-digit OTP code sent to Gmail is valid and unexpired."""
    otp_record = db.query(models.EmailOTP).filter(
        models.EmailOTP.email == payload.email,
        models.EmailOTP.otp_code == payload.otp_code.strip(),
        models.EmailOTP.purpose == payload.purpose,
        models.EmailOTP.is_used == False,
    ).order_by(models.EmailOTP.id.desc()).first()

    if not otp_record:
        # Also check PasswordResetToken table for fallback
        reset_rec = db.query(models.PasswordResetToken).join(models.User).filter(
            models.User.email == payload.email,
            models.PasswordResetToken.otp_code == payload.otp_code.strip(),
            models.PasswordResetToken.is_used == False,
        ).order_by(models.PasswordResetToken.id.desc()).first()
        if not reset_rec or reset_rec.expires_at < datetime.utcnow():
            return VerifyOTPResponse(valid=False, detail="Invalid or expired OTP code. Please check your Gmail or request a new OTP.")
        return VerifyOTPResponse(valid=True, email=payload.email, token=reset_rec.token)

    if otp_record.expires_at < datetime.utcnow():
        return VerifyOTPResponse(valid=False, detail="This OTP code has expired. Please request a fresh OTP.")

    # Find associated token if any
    token_rec = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == otp_record.user_id,
        models.PasswordResetToken.is_used == False,
    ).order_by(models.PasswordResetToken.id.desc()).first()
    token_str = token_rec.token if token_rec else None

    return VerifyOTPResponse(valid=True, email=payload.email, token=token_str)


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Resets the password using either a valid reset token OR a 6-digit OTP."""
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    user = None
    # 1. Check via token if provided
    if payload.token:
        record = db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.token == payload.token
        ).first()
        if record and not record.is_used and record.expires_at >= datetime.utcnow():
            user = record.user
            record.is_used = True

    # 2. Check via OTP + email if provided
    if not user and payload.otp_code and payload.email:
        otp_rec = db.query(models.EmailOTP).filter(
            models.EmailOTP.email == payload.email,
            models.EmailOTP.otp_code == payload.otp_code.strip(),
            models.EmailOTP.purpose == "reset_password",
            models.EmailOTP.is_used == False,
        ).order_by(models.EmailOTP.id.desc()).first()

        if otp_rec and otp_rec.expires_at >= datetime.utcnow():
            user = otp_rec.user
            otp_rec.is_used = True
            # Invalidate any matching token records too
            db.query(models.PasswordResetToken).filter(
                models.PasswordResetToken.user_id == user.id,
                models.PasswordResetToken.is_used == False,
            ).update({"is_used": True})

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token or OTP code.")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password has been successfully updated. You may now log in."}


@router.post("/reset-password-otp")
def reset_password_otp(payload: ResetPasswordOTPRequest, db: Session = Depends(get_db)):
    """Resets the password directly using the 6-digit OTP sent to Gmail."""
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    otp_rec = db.query(models.EmailOTP).filter(
        models.EmailOTP.email == payload.email,
        models.EmailOTP.otp_code == payload.otp_code.strip(),
        models.EmailOTP.purpose == "reset_password",
        models.EmailOTP.is_used == False,
    ).order_by(models.EmailOTP.id.desc()).first()

    user = None
    if otp_rec and otp_rec.expires_at >= datetime.utcnow():
        user = otp_rec.user
        otp_rec.is_used = True
    else:
        # Fallback check on PasswordResetToken
        reset_rec = db.query(models.PasswordResetToken).join(models.User).filter(
            models.User.email == payload.email,
            models.PasswordResetToken.otp_code == payload.otp_code.strip(),
            models.PasswordResetToken.is_used == False,
        ).order_by(models.PasswordResetToken.id.desc()).first()
        if reset_rec and reset_rec.expires_at >= datetime.utcnow():
            user = reset_rec.user
            reset_rec.is_used = True

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP code.")

    user.hashed_password = hash_password(payload.new_password)
    # Invalidate all unused tokens for this user
    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user.id,
        models.PasswordResetToken.is_used == False,
    ).update({"is_used": True})
    db.commit()

    return {"message": "Password has been successfully updated. You may now log in."}


@router.post("/send-login-otp")
def send_login_otp(payload: SendLoginOTPRequest, db: Session = Depends(get_db)):
    """
    Sends a 6-digit login verification OTP to the user's Gmail/work email.
    """
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        # Generic response to prevent enumeration
        return {
            "message": "If this email is registered, a 6-digit login OTP has been sent to your inbox.",
            "email_sent": False,
        }

    # Invalidate previous unused login OTPs
    db.query(models.EmailOTP).filter(
        models.EmailOTP.user_id == user.id,
        models.EmailOTP.purpose == "login",
        models.EmailOTP.is_used == False,
    ).update({"is_used": True})

    otp_code = generate_otp_code()
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    email_otp = models.EmailOTP(
        user_id=user.id,
        email=user.email,
        otp_code=otp_code,
        purpose="login",
        expires_at=expires_at,
        is_used=False,
    )
    db.add(email_otp)
    db.commit()

    email_sent, _ = send_verification_otp_email(
        to_email=user.email,
        otp_code=otp_code,
        purpose="login",
    )
    if not email_sent:
        email_otp.is_used = True
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Could not send the verification email. Please try again later.",
        )

    return {
        "message": "If an account with that email exists, we have sent a login OTP.",
    }


@router.post("/verify-login-otp", response_model=AuthResponse)
def verify_login_otp(payload: VerifyLoginOTPRequest, db: Session = Depends(get_db)):
    """
    Authenticates a user via 6-digit OTP received in Gmail.
    """
    otp_rec = db.query(models.EmailOTP).filter(
        models.EmailOTP.email == payload.email,
        models.EmailOTP.otp_code == payload.otp_code.strip(),
        models.EmailOTP.purpose == "login",
        models.EmailOTP.is_used == False,
    ).order_by(models.EmailOTP.id.desc()).first()

    if not otp_rec:
        raise HTTPException(status_code=401, detail="Invalid OTP code. Please check your Gmail.")

    if otp_rec.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="This OTP code has expired. Please request a new one.")

    user = otp_rec.user
    otp_rec.is_used = True
    db.commit()

    startup = db.query(models.Startup).filter(models.Startup.user_id == user.id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="No startup profile found for this account.")

    return AuthResponse(user_id=user.id, startup_id=startup.id, company_name=startup.company_name)
