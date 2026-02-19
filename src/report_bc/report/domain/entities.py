from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import ulid

from src.report_bc.report.domain.enums import ReportStatus, ReportType


@dataclass
class Report:
    id: str
    company_id: str
    requested_by: str
    type: ReportType
    status: ReportStatus
    parameters: Optional[dict[str, Any]] = None
    storage_key: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        requested_by: str,
        type: str,
        parameters: Optional[dict[str, Any]] = None,
        id: Optional[str] = None,
    ) -> "Report":
        report_type = ReportType(type)
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            requested_by=requested_by,
            type=report_type,
            status=ReportStatus.PENDING,
            parameters=parameters,
        )
