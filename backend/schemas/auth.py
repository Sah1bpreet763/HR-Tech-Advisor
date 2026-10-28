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


class VerifyTokenResponse(BaseModel):
    valid: bool
    email: Optional[str] = None
    detail: Optional[str] = None


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str
    purpose: Optional[str] = "reset_password"


class VerifyOTPResponse(BaseModel):
    valid: bool
    email: Optional[str] = None
    token: Optional[str] = None
    detail: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: Optional[str] = None
    email: Optional[EmailStr] = None
    otp_code: Optional[str] = None
    new_password: str


class ResetPasswordOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str


class SendLoginOTPRequest(BaseModel):
    email: EmailStr


class VerifyLoginOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str
