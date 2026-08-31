from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr | None = None
    phone_number: str | None = None
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one uppercase letter and one digit")
        return v

    @field_validator("email", "phone_number")
    @classmethod
    def require_identifier(cls, v: str | None) -> str | None:
        return v


class LoginRequest(BaseModel):
    email: EmailStr | None = None
    phone_number: str | None = None
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class MfaRequiredResponse(BaseModel):
    requires_2fa: bool = True
    mfa_token: str
    expires_in: int


class TotpVerifyRequest(BaseModel):
    mfa_token: str
    code: str


class TotpEnableRequest(BaseModel):
    code: str


class TotpDisableRequest(BaseModel):
    password: str


class TotpSetupResponse(BaseModel):
    secret: str
    otpauth_url: str
    recovery_codes: list[str]


class TotpStatusResponse(BaseModel):
    enabled: bool


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr | None = None
    phone_number: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str


class VerifyOtpRequest(BaseModel):
    phone_number: str
    otp: str


class SendOtpRequest(BaseModel):
    phone_number: str


class UserAccountResponse(BaseModel):
    id: str
    email: str | None = None
    phone_number: str | None = None
    account_status: str
    role: str
    is_banned: bool
    email_verified: bool
    phone_verified: bool
    created_at: str | None = None
