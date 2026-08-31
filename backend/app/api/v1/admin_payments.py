from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_request_context, get_session, require_permission
from app.db.models import User
from app.repositories.billing_repo import PaymentRepository
from app.schemas.admin import AdminActionResponse, PaymentDetail, PaymentRow
from app.schemas.common import ApiResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/admin/payments", tags=["admin", "payments"])

can_read = require_permission("payments.read")
can_refund = require_permission("payments.refund")


def _meta(total: int, limit: int, offset: int) -> dict[str, Any]:
    return {"total": total, "limit": limit, "offset": offset, "count": min(total - offset, limit)}


@router.get("", summary="List payments (admin)", response_model=ApiResponse[list[PaymentRow]])
async def list_payments(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    status: str | None = Query(default=None),
    payment_type: str | None = Query(default=None),
    user_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[PaymentRow]]:
    statuses = status.split(",") if status else None
    rows, total = await PaymentRepository(session).admin_search(
        statuses=statuses,
        payment_type=payment_type,
        user_id=user_id,
        search=search,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[PaymentRow(**r) for r in rows], meta=_meta(total, limit, offset))


@router.get("/{payment_id}", summary="Payment detail (admin)", response_model=ApiResponse[PaymentDetail])
async def payment_detail(
    payment_id: UUID,
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[PaymentDetail]:
    payment, user_email = await PaymentRepository(session).get_detail(payment_id)
    if payment is None:
        from app.api.errors import NotFoundError

        raise NotFoundError("Payment not found", code="PAYMENT_NOT_FOUND")
    return ApiResponse(
        data=PaymentDetail(
            id=str(payment.id),
            user_id=str(payment.user_id),
            user_name=user_email,
            amount=payment.amount,
            currency=payment.currency,
            payment_type=payment.payment_type,
            status=payment.status.value,
            provider=payment.provider,
            provider_payment_id=payment.provider_payment_id,
            created_at=payment.created_at,
            paid_at=payment.paid_at,
            meta=payment.meta,
        )
    )


@router.post(
    "/{payment_id}/refund",
    summary="Refund a successful payment (audited)",
    response_model=ApiResponse[AdminActionResponse],
)
async def refund_payment(
    payment_id: UUID,
    payload: dict,
    request: Request,
    admin: User = Depends(can_refund),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    await PaymentService(session).refund(
        admin,
        payment_id,
        reason=payload.get("reason"),
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="refunded", message="Payment refunded"))
