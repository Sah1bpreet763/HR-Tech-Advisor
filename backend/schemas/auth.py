"""Pydantic schemas for registration and login."""
from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    industry: Optional[str] = None
    team_size: Optional[int] = None
    growth_stage: Optional[str] = None
    hr_budget_monthly: Optional[float] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    user_id: int
    startup_id: int
    company_name: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_url: Optional[str] = None  # Provided in dev/testing mode if SMTP is not configured
    email_sent: bool


class VerifyTokenResponse(BaseModel):
    valid: bool
    email: Optional[str] = None
    detail: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

