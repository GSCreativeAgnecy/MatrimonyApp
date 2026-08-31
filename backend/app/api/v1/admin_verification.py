from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_any_permission, require_permission
from app.api.errors import ForbiddenError, NotFoundError
from app.db.models import User
from app.repositories.verification_repo import VerificationRepository
from app.schemas.admin import AdminActionResponse, JobVerificationRow
from app.schemas.common import ApiResponse
from app.services.permission_service import PermissionService
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/admin/verifications", tags=["admin", "verification"])

can_read = require_permission("job_verification.read")
can_review = require_any_permission("job_verification.approve", "job_verification.reject")


def _meta(total: int, limit: int, offset: int) -> dict[str, Any]:
    return {"total": total, "limit": limit, "offset": offset, "count": min(total - offset, limit)}


@router.get("/job", summary="List job verifications", response_model=ApiResponse[list[JobVerificationRow]])
async def list_job_verifications(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[JobVerificationRow]]:
    statuses = status.split(",") if status else None
    rows, total = await VerificationRepository(session).admin_list(
        statuses=statuses, search=search, limit=limit, offset=offset
    )
    return ApiResponse(data=[JobVerificationRow(**r) for r in rows], meta=_meta(total, limit, offset))


@router.get("/job/{verification_id}", summary="Job verification detail", response_model=ApiResponse[dict])
async def job_verification_detail(
    verification_id: UUID,
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    from app.db.models import JobVerification, Payment

    verification = await session.get(JobVerification, verification_id)
    if verification is None:
        raise NotFoundError("Verification not found", code="VERIFICATION_NOT_FOUND")
    payment = await session.get(Payment, verification.payment_id) if verification.payment_id else None
    return ApiResponse(
        data={
            "id": str(verification.id),
            "user_id": str(verification.user_id),
            "employment_type": verification.employment_type.value,
            "employer_name": verification.employer_name,
            "job_title": verification.job_title,
            "country": verification.country,
            "verification_status": verification.verification_status.value,
            "amount_paid": float(verification.amount_paid) if verification.amount_paid is not None else None,
            "currency": verification.currency,
            "submitted_at": verification.submitted_at,
            "verified_at": verification.verified_at,
            "expires_at": verification.expires_at,
            "reviewer_notes": verification.reviewer_notes,
            "rejection_reason": verification.rejection_reason,
            "reviewer_id": str(verification.reviewer_id) if verification.reviewer_id else None,
            "payment_id": str(verification.payment_id) if verification.payment_id else None,
            "payment_status": payment.status.value if payment else None,
            "created_at": verification.created_at,
        }
    )


@router.post(
    "/job/{verification_id}/review", summary="Approve or reject a job verification", response_model=ApiResponse[dict]
)
async def review_job_verification(
    verification_id: UUID,
    payload: dict,
    request: Request,
    admin: User = Depends(can_review),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    approve = bool(payload.get("approve", False))
    required = "job_verification.approve" if approve else "job_verification.reject"
    allowed = await PermissionService(session).permissions_for_role(admin.role)
    if required not in allowed:
        raise ForbiddenError("Insufficient permissions", code="FORBIDDEN")

    service = VerificationService(session)
    verification = await service.review(
        admin,
        verification_id,
        approve=approve,
        rejection_reason=payload.get("rejection_reason"),
        reviewer_notes=payload.get("admin_notes"),
        expires_in_days=int(payload.get("expires_in_days", 365)),
    )
    await session.commit()
    return ApiResponse(
        data={
            "id": str(verification.id),
            "verification_status": verification.verification_status.value,
            "message": "Approved" if approve else "Rejected",
        }
    )


@router.post(
    "/job/{verification_id}/request-info",
    summary="Request more information from the user",
    response_model=ApiResponse[AdminActionResponse],
)
async def request_more_info(
    verification_id: UUID,
    payload: dict,
    request: Request,
    admin: User = Depends(can_review),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    reason = payload.get("reason") or payload.get("admin_notes") or "More information required"
    await VerificationService(session).request_more_info(admin, verification_id, reason=reason)
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="info_requested", message="More information requested"))
