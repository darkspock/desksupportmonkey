from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.incident_bc.incident.domain.exceptions import IncidentNotFoundError
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class ReportWithCountdownDto:
    id: str
    report_type: str
    status: str
    deadline_at: Optional[datetime]
    generated_at: Optional[datetime]
    submitted_at: Optional[datetime]
    file_path: Optional[str]
    time_remaining_seconds: Optional[int]
    elapsed_percentage: float


@dataclass
class ListReportsQuery(Query):
    incident_id: str
    company_id: str


class ListReportsQueryHandler(
    QueryHandler[ListReportsQuery, list[ReportWithCountdownDto]]
):
    def __init__(self, incident_repo: IncidentRepositoryInterface):
        self.incident_repo = incident_repo

    def handle(self, query: ListReportsQuery) -> list[ReportWithCountdownDto]:
        incident = self.incident_repo.find_by_id(
            query.incident_id, query.company_id
        )
        if not incident:
            raise IncidentNotFoundError(query.incident_id)

        reports = self.incident_repo.find_reports_by_incident(query.incident_id)
        now = datetime.now(timezone.utc)

        result: list[ReportWithCountdownDto] = []
        for r in reports:
            deadline = r.deadline_at
            detected = incident.detected_at

            # Compute time remaining
            remaining = deadline - now
            time_remaining_seconds = max(int(remaining.total_seconds()), 0)

            # Compute elapsed percentage
            total_duration = (deadline - detected).total_seconds()
            elapsed = (now - detected).total_seconds()
            if total_duration > 0:
                elapsed_percentage = min(
                    round((elapsed / total_duration) * 100, 1), 100.0
                )
            else:
                elapsed_percentage = 100.0

            result.append(
                ReportWithCountdownDto(
                    id=r.id,
                    report_type=r.report_type.value,
                    status=r.status.value,
                    deadline_at=deadline,
                    generated_at=r.generated_at,
                    submitted_at=r.submitted_at,
                    file_path=r.file_path,
                    time_remaining_seconds=time_remaining_seconds,
                    elapsed_percentage=elapsed_percentage,
                )
            )
        return result
