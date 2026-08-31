from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session, rate_limit
from app.db.models import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MfaRequiredResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendOtpRequest,
    TokenResponse,
    TotpDisableRequest,
    TotpEnableRequest,
    TotpSetupResponse,
    TotpStatusResponse,
    TotpVerifyRequest,
    UserAccountResponse,
    VerifyOtpRequest,
)
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService
from app.services.totp_service import TotpService

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_data(data: dict) -> ApiResponse[TokenResponse]:
    return ApiResponse(data=TokenResponse(**data))


@router.post("/register", summary="Register a new account", response_model=ApiResponse[TokenResponse])
async def register(
    payload: RegisterRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(rate_limit("otp")),
) -> ApiResponse[TokenResponse]:
    service = AuthService(session)
    user = await service.register(email=payload.email, phone_number=payload.phone_number, password=payload.password)
    tokens = await service.create_token_pair(user.id)
    await session.commit()
    return _token_data(tokens)


@router.post(
    "/login",
    summary="Log in",
    response_model=ApiResponse[TokenResponse | MfaRequiredResponse],
)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(rate_limit("login")),
) -> ApiResponse[TokenResponse] | ApiResponse[MfaRequiredResponse]:
    service = AuthService(session)
    user, mfa_required = await service.login(
        email=payload.email, phone_number=payload.phone_number, password=payload.password
    )
    if mfa_required:
        from app.security.jwt import MFA_TOKEN_EXPIRE_MINUTES, create_mfa_token

        mfa_token = create_mfa_token(str(user.id))
        await session.commit()
        return ApiResponse(data=MfaRequiredResponse(mfa_token=mfa_token, expires_in=MFA_TOKEN_EXPIRE_MINUTES * 60))
    tokens = await service.create_token_pair(user.id)
    await session.commit()
    return _token_data(tokens)


@router.post(
    "/totp/verify", summary="Complete login with a TOTP/recovery code", response_model=ApiResponse[TokenResponse]
)
async def totp_verify(
    payload: TotpVerifyRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(rate_limit("otp")),
) -> ApiResponse[TokenResponse]:
    service = AuthService(session)
    tokens = await service.complete_mfa_login(payload.mfa_token, payload.code)
    await session.commit()
    return _token_data(tokens)


@router.post(
    "/totp/setup", summary="Generate a TOTP secret + recovery codes", response_model=ApiResponse[TotpSetupResponse]
)
async def totp_setup(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[TotpSetupResponse]:
    data = await TotpService(session).setup(user)
    await session.commit()
    return ApiResponse(data=TotpSetupResponse(**data))


@router.get(
    "/totp/status", summary="Whether TOTP is enabled for the account", response_model=ApiResponse[TotpStatusResponse]
)
async def totp_status(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[TotpStatusResponse]:
    enabled = await TotpService(session).is_enabled(user.id)
    return ApiResponse(data=TotpStatusResponse(enabled=enabled))


@router.post("/totp/enable", summary="Enable TOTP after confirming a live code", response_model=ApiResponse[dict])
async def totp_enable(
    payload: TotpEnableRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    await TotpService(session).enable(user, payload.code)
    await session.commit()
    return ApiResponse(data={"status": "enabled"})


@router.post("/totp/disable", summary="Disable TOTP (password required)", response_model=ApiResponse[dict])
async def totp_disable(
    payload: TotpDisableRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    await TotpService(session).disable(user, payload.password)
    await session.commit()
    return ApiResponse(data={"status": "disabled"})


@router.post("/refresh", summary="Rotate the refresh token", response_model=ApiResponse[TokenResponse])
async def refresh(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[TokenResponse]:
    service = AuthService(session)
    tokens = await service.refresh(payload.refresh_token)
    await session.commit()
    return _token_data(tokens)


@router.post("/logout", summary="Log out and revoke the refresh token", response_model=ApiResponse[dict])
async def logout(
    payload: LogoutRequest,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = AuthService(session)
    await service.logout(payload.refresh_token)
    await session.commit()
    return ApiResponse(data={"logged_out": True})


@router.post("/forgot-password", summary="Request a password reset", response_model=ApiResponse[dict])
async def forgot_password(
    payload: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(rate_limit("otp")),
) -> ApiResponse[dict]:
    service = AuthService(session)
    await service.forgot_password(email=payload.email, phone_number=payload.phone_number)
    await session.commit()
    return ApiResponse(data={"status": "ok"})


@router.post("/reset-password", summary="Reset the password with a token", response_model=ApiResponse[dict])
async def reset_password(
    payload: ResetPasswordRequest,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = AuthService(session)
    await service.reset_password(payload.token, payload.new_password)
    await session.commit()
    return ApiResponse(data={"status": "ok"})


@router.post("/verify-email", summary="Verify an email address", response_model=ApiResponse[dict])
async def verify_email(payload: dict, session: AsyncSession = Depends(get_session)) -> ApiResponse[dict]:
    service = AuthService(session)
    await service.verify_email(payload.get("token", ""))
    await session.commit()
    return ApiResponse(data={"status": "ok"})


@router.post("/send-otp", summary="Send an SMS OTP", response_model=ApiResponse[dict])
async def send_otp(
    payload: SendOtpRequest,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(rate_limit("otp")),
) -> ApiResponse[dict]:
    service = AuthService(session)
    await service.send_otp(payload.phone_number)
    await session.commit()
    return ApiResponse(data={"status": "ok"})


@router.post("/verify-otp", summary="Verify an SMS OTP", response_model=ApiResponse[dict])
async def verify_otp(payload: VerifyOtpRequest, session: AsyncSession = Depends(get_session)) -> ApiResponse[dict]:
    service = AuthService(session)
    await service.verify_otp(payload.phone_number, payload.otp)
    await session.commit()
    return ApiResponse(data={"status": "ok"})


@router.get("/me", summary="Current user account", response_model=ApiResponse[UserAccountResponse])
async def me(user: User = Depends(get_current_user)) -> ApiResponse[UserAccountResponse]:
    return ApiResponse(
        data=UserAccountResponse(
            id=str(user.id),
            email=user.email,
            phone_number=user.phone_number,
            account_status=user.account_status.value,
            role=user.role.value,
            is_banned=user.is_banned,
            email_verified=user.email_verified_at is not None,
            phone_verified=user.phone_verified_at is not None,
            created_at=user.created_at.isoformat() if user.created_at else None,
        )
    )


@router.post("/change-password", summary="Change the current user's password", response_model=ApiResponse[dict])
async def change_password(
    payload: dict,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = AuthService(session)
    await service.change_password(user, payload["old_password"], payload["new_password"])
    await session.commit()
    return ApiResponse(data={"status": "ok"})
