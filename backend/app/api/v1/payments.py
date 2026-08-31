from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.api.errors import UnauthorizedError
from app.schemas.common import ApiResponse
from app.services.payment_service import PaymentService, build_provider

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "/webhook/{provider}",
    summary="Provider webhook endpoint (verifies signature, then processes)",
    response_model=ApiResponse[dict],
)
async def payment_webhook(
    provider: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    provider_obj = build_provider()
    if provider_obj.name != provider:
        raise UnauthorizedError("Unknown payment provider", code="UNKNOWN_PROVIDER")

    try:
        payload = await request.json()
    except Exception:
        raise UnauthorizedError("Invalid webhook payload", code="INVALID_WEBHOOK") from None

    headers = {k.lower(): v for k, v in request.headers.items()}
    if not await provider_obj.verify_webhook(payload, headers):
        raise UnauthorizedError("Webhook signature verification failed", code="WEBHOOK_UNAUTHORIZED")

    service = PaymentService(session)
    result = await service.handle_webhook(provider, payload)
    await session.commit()
    return ApiResponse(data=result)
