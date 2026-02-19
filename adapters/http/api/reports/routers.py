import ulid
from fastapi import APIRouter, Depends, HTTPException, Query, status

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.reports.dependencies import get_report_repo
from adapters.http.api.reports.schemas import (
    CreateReportRequest,
    DownloadResponse,
    ReportListItemResponse,
    ReportResponse,
)
from adapters.http.schemas.responses import PaginationMeta
from core.config import settings
from core.storage import S3StorageService
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.report_bc.report.application.commands.request_report import (
    RequestReportCommand,
    RequestReportCommandHandler,
)
from src.report_bc.report.application.queries.get_report import (
    GetReportQuery,
    GetReportQueryHandler,
    ReportNotFoundError,
)
from src.report_bc.report.application.queries.list_reports import (
    ListReportsQuery,
    ListReportsQueryHandler,
)
from src.report_bc.report.domain.enums import ReportStatus
from src.report_bc.report.infrastructure.repository import ReportRepository

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])

admin_dep = require_role(UserRole.ADMIN)


def _to_report_response(report: object) -> ReportResponse:
    return ReportResponse(
        id=report.id,
        type=report.type.value,
        status=report.status.value,
        parameters=report.parameters,
        created_at=report.created_at,
        completed_at=report.completed_at,
    )


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def create_report(
    body: CreateReportRequest,
    current_user: User = Depends(admin_dep),
    report_repo: ReportRepository = Depends(get_report_repo),
):
    report_id = str(ulid.new())
    handler = RequestReportCommandHandler(report_repo=report_repo)
    try:
        handler.handle(
            RequestReportCommand(
                company_id=current_user.company_id,
                requested_by=current_user.id,
                type=body.type,
                parameters=body.parameters,
                id=report_id,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    query_handler = GetReportQueryHandler(report_repo=report_repo)
    report = query_handler.handle(
        GetReportQuery(report_id=report_id, company_id=current_user.company_id)
    )
    return {"data": _to_report_response(report).model_dump(mode="json")}


@router.get("")
def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(admin_dep),
    report_repo: ReportRepository = Depends(get_report_repo),
):
    handler = ListReportsQueryHandler(report_repo=report_repo)
    reports, total = handler.handle(
        ListReportsQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
        )
    )
    return {
        "data": [
            ReportListItemResponse(
                id=r.id,
                type=r.type.value,
                status=r.status.value,
                created_at=r.created_at,
                completed_at=r.completed_at,
            ).model_dump(mode="json")
            for r in reports
        ],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.get("/{report_id}")
def get_report(
    report_id: str,
    current_user: User = Depends(admin_dep),
    report_repo: ReportRepository = Depends(get_report_repo),
):
    handler = GetReportQueryHandler(report_repo=report_repo)
    try:
        report = handler.handle(
            GetReportQuery(report_id=report_id, company_id=current_user.company_id)
        )
    except ReportNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    return {
        "data": ReportResponse(
            id=report.id,
            type=report.type.value,
            status=report.status.value,
            parameters=report.parameters,
            created_at=report.created_at,
            completed_at=report.completed_at,
            error_message=report.error_message,
        ).model_dump(mode="json")
    }


@router.get("/{report_id}/download")
def download_report(
    report_id: str,
    current_user: User = Depends(admin_dep),
    report_repo: ReportRepository = Depends(get_report_repo),
):
    report = report_repo.find_by_id(report_id, current_user.company_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Report is {report.status.value}",
        )

    storage = S3StorageService()
    url = storage.get_signed_url(report.storage_key, settings.s3.S3_SIGNED_URL_EXPIRY)
    return {
        "data": DownloadResponse(download_url=url).model_dump()
    }
