from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_request_context, get_session, require_permission
from app.db.enums import PhotoVerificationStatus
from app.db.models import User
from app.schemas.admin import (
    AdminActionResponse,
    PhotoRow,
    ReportDetail,
    ReportRow,
)
from app.schemas.common import ApiResponse
from app.services.admin_user_service import AdminUserService
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.photo_service import PhotoService
from app.services.profile_service import ProfileService
from app.services.report_service import ReportService

router = APIRouter(prefix="/admin", tags=["admin", "moderation"])

can_read_profiles = require_permission("profiles.read")
can_moderate_profiles = require_permission("profiles.moderate")
can_moderate_photos = require_permission("photos.moderate")
can_read_reports = require_permission("reports.read")
can_resolve_reports = require_permission("reports.resolve")


def _meta(total: int, limit: int, offset: int) -> dict[str, Any]:
    return {"total": total, "limit": limit, "offset": offset, "count": min(total - offset, limit)}


# ---------- profiles ----------


@router.get("/profiles", summary="List profiles for moderation", response_model=ApiResponse[list[dict]])
async def list_profiles(
    admin: User = Depends(can_read_profiles),
    session: AsyncSession = Depends(get_session),
    search: str | None = Query(default=None),
    incomplete: bool | None = Query(default=None),
    reported: bool | None = Query(default=None),
    review_status: str | None = Query(default=None),
    recently_updated: bool | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[dict]]:
    rows, total = await ProfileService(session).admin_list(
        search=search,
        incomplete=incomplete,
        reported=reported,
        review_status=review_status,
        recently_updated=recently_updated,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=rows, meta=_meta(total, limit, offset))


@router.get("/profiles/{user_id}", summary="Full profile review payload", response_model=ApiResponse[dict])
async def profile_detail(
    user_id: UUID,
    admin: User = Depends(can_read_profiles),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    data = await AdminUserService(session).profile(user_id)
    reports = await AdminUserService(session).reports(user_id)
    verifications = await AdminUserService(session).verifications(user_id)
    data["reports"] = reports
    data["verifications"] = verifications
    return ApiResponse(data=data)


@router.post(
    "/profiles/{user_id}/moderate",
    summary="Approve/reject/request changes/suspend a profile",
    response_model=ApiResponse[AdminActionResponse],
)
async def moderate_profile(
    user_id: UUID,
    payload: dict,
    request: Request,
    admin: User = Depends(can_moderate_profiles),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    await ProfileService(session).moderate(
        admin,
        user_id,
        action=payload.get("action", ""),
        reason=payload.get("reason"),
    )
    await AuditService(session).record(
        action="profile.moderate",
        actor_user_id=admin.id,
        entity_type="profile",
        entity_id=str(user_id),
        metadata={"action": payload.get("action"), "reason": payload.get("reason")},
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="updated", message="Profile moderation recorded"))


# ---------- photos ----------


@router.get("/photos", summary="List photos for moderation", response_model=ApiResponse[list[PhotoRow]])
async def list_photos(
    admin: User = Depends(can_moderate_photos),
    session: AsyncSession = Depends(get_session),
    status: PhotoVerificationStatus | None = Query(default=None),
    user_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[PhotoRow]]:
    rows, total = await PhotoService(session).admin_list(
        status=status, user_id=user_id, search=search, limit=limit, offset=offset
    )
    return ApiResponse(data=[PhotoRow(**r) for r in rows], meta=_meta(total, limit, offset))


@router.post(
    "/photos/{photo_id}/review",
    summary="Approve/reject/request replacement for a photo",
    response_model=ApiResponse[AdminActionResponse],
)
async def review_photo(
    photo_id: UUID,
    payload: dict,
    request: Request,
    admin: User = Depends(can_moderate_photos),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    await PhotoService(session).review(admin, photo_id, action=payload.get("action", ""), reason=payload.get("reason"))
    await AuditService(session).record(
        action=f"photo.{payload.get('action')}",
        actor_user_id=admin.id,
        entity_type="photo",
        entity_id=str(photo_id),
        metadata={"reason": payload.get("reason")},
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="updated", message="Photo review recorded"))


# ---------- profile shares ----------


@router.get("/profile-shares", summary="List profile shares", response_model=ApiResponse[list[dict]])
async def list_profile_shares(
    admin: User = Depends(can_read_profiles),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[dict]]:
    from sqlalchemy import func, select
    from sqlalchemy.orm import aliased

    from app.db.models import ProfileShare
    from app.db.models import User as UserModel

    owner = aliased(UserModel)
    shared = aliased(UserModel)
    stmt = (
        select(ProfileShare, owner.email.label("owner_email"), shared.email.label("shared_email"))
        .outerjoin(owner, owner.id == ProfileShare.owner_user_id)
        .outerjoin(shared, shared.id == ProfileShare.shared_with_user_id)
        .order_by(ProfileShare.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    count_stmt = select(func.count()).select_from(ProfileShare)
    total = int((await session.execute(count_stmt)).scalar_one())
    rows = (await session.execute(stmt)).all()
    return ApiResponse(
        data=[
            {
                "id": str(s.id),
                "owner_user_id": str(s.owner_user_id),
                "shared_with_user_id": str(s.shared_with_user_id),
                "owner_email": owner_email,
                "shared_email": shared_email,
                "permission": s.permission.value,
                "expires_at": s.expires_at,
                "revoked_at": s.revoked_at,
                "created_at": s.created_at,
            }
            for s, owner_email, shared_email in rows
        ],
        meta=_meta(total, limit, offset),
    )


# ---------- reports ----------


def _report_row(report, reporter_email: str | None, reported_email: str | None) -> dict:
    return {
        "id": str(report.id),
        "reporter_id": str(report.reporter_id),
        "reported_user_id": str(report.reported_user_id),
        "reporter_name": reporter_email,
        "reported_name": reported_email,
        "reason": report.reason,
        "description": report.description,
        "status": report.status,
        "reviewed_by": str(report.reviewed_by) if report.reviewed_by else None,
        "reviewed_at": report.reviewed_at,
        "created_at": report.created_at,
    }


@router.get("/reports", summary="List reports", response_model=ApiResponse[list[ReportRow]])
async def list_reports(
    admin: User = Depends(can_read_reports),
    session: AsyncSession = Depends(get_session),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[ReportRow]]:
    statuses = status.split(",") if status else None
    rows, total = await ReportService(session).repo.admin_list(
        statuses=statuses, search=search, limit=limit, offset=offset
    )
    return ApiResponse(
        data=[ReportRow(**_report_row(r, re, re2)) for r, re, re2 in rows],
        meta=_meta(total, limit, offset),
    )


@router.get("/reports/{report_id}", summary="Report detail with history", response_model=ApiResponse[ReportDetail])
async def report_detail(
    report_id: UUID,
    admin: User = Depends(can_read_reports),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[ReportDetail]:
    report, reporter, reported = await ReportService(session).repo.detail(report_id)
    if report is None:
        from app.api.errors import NotFoundError

        raise NotFoundError("Report not found", code="REPORT_NOT_FOUND")
    history = await ReportService(session).history(report_id)
    row = _report_row(report, reporter.email if reporter else None, reported.email if reported else None)
    row["reporter_email"] = reporter.email if reporter else None
    row["reported_email"] = reported.email if reported else None
    row["history"] = history
    return ApiResponse(data=ReportDetail(**row))


@router.post("/reports/{report_id}/assign", summary="Assign a report", response_model=ApiResponse[AdminActionResponse])
async def assign_report(
    report_id: UUID,
    payload: dict,
    request: Request,
    admin: User = Depends(can_resolve_reports),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    await ReportService(session).assign(admin, report_id, assignee_id=UUID(payload["assignee_id"]))
    await AuditService(session).record(
        action="report.assign",
        actor_user_id=admin.id,
        entity_type="report",
        entity_id=str(report_id),
        metadata={"assignee_id": payload.get("assignee_id")},
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="assigned", message="Report assigned"))


@router.post(
    "/reports/{report_id}/review",
    summary="Transition a report to a status",
    response_model=ApiResponse[AdminActionResponse],
)
async def review_report(
    report_id: UUID,
    payload: dict,
    request: Request,
    admin: User = Depends(can_resolve_reports),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    await ReportService(session).transition(
        admin, report_id, status=payload.get("status", ""), reason=payload.get("reason")
    )
    await AuditService(session).record(
        action="report.review",
        actor_user_id=admin.id,
        entity_type="report",
        entity_id=str(report_id),
        metadata={"status": payload.get("status"), "reason": payload.get("reason")},
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="updated", message="Report updated"))


@router.post(
    "/reports/{report_id}/warn", summary="Warn the reported user", response_model=ApiResponse[AdminActionResponse]
)
async def warn_reported_user(
    report_id: UUID,
    payload: dict,
    request: Request,
    admin: User = Depends(can_resolve_reports),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    report = await ReportService(session).get_or_404(report_id)
    await NotificationService(session).create(
        report.reported_user_id,
        type="SYSTEM",
        title="Account warning",
        body=payload.get("message", "Our moderation team has reviewed your account."),
    )
    await AuditService(session).record(
        action="report.warn",
        actor_user_id=admin.id,
        entity_type="report",
        entity_id=str(report_id),
        metadata={"message": payload.get("message"), "reported_user_id": str(report.reported_user_id)},
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="warned", message="Warning sent to user"))


@router.post(
    "/reports/{report_id}/suspend",
    summary="Suspend the reported user",
    response_model=ApiResponse[AdminActionResponse],
)
async def suspend_reported_user(
    report_id: UUID,
    payload: dict,
    request: Request,
    admin: User = Depends(can_resolve_reports),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    service = AdminUserService(session)
    report = await ReportService(session).get_or_404(report_id)
    await service.suspend(
        admin,
        report.reported_user_id,
        reason=payload.get("reason", "Suspended following a report"),
        duration_minutes=payload.get("duration_minutes"),
        notes=payload.get("admin_notes"),
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    report.status = "RESOLVED"
    report.reviewed_by = admin.id
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="suspended", message="User suspended and report resolved"))


@router.post(
    "/reports/{report_id}/ban", summary="Ban the reported user", response_model=ApiResponse[AdminActionResponse]
)
async def ban_reported_user(
    report_id: UUID,
    payload: dict,
    request: Request,
    admin: User = Depends(can_resolve_reports),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    service = AdminUserService(session)
    report = await ReportService(session).get_or_404(report_id)
    await service.ban(
        admin,
        report.reported_user_id,
        reason=payload.get("reason", "Banned following a report"),
        notes=payload.get("admin_notes"),
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    report.status = "RESOLVED"
    report.reviewed_by = admin.id
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="banned", message="User banned and report resolved"))
