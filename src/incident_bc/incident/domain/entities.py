from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import ulid

from src.incident_bc.incident.domain.enums import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    ReportStatus,
    ReportType,
    TimelineEventType,
    VALID_STATUS_TRANSITIONS,
)
from src.incident_bc.incident.domain.exceptions import (
    CloseReasonRequiredError,
    IncidentClosedError,
    InvalidStatusTransitionError,
    ReportNotGeneratedError,
)


@dataclass
class SecurityIncident:
    id: str
    company_id: str
    title: str
    description: str
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    reported_by: str
    detected_at: datetime
    attack_vector: Optional[str] = None
    data_breach_scope: Optional[str] = None
    assigned_to: Optional[str] = None
    close_reason: Optional[str] = None
    custom_fields_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        title: str,
        description: str,
        incident_type: IncidentType,
        severity: IncidentSeverity,
        detected_at: datetime,
        reported_by: str,
        attack_vector: Optional[str] = None,
        data_breach_scope: Optional[str] = None,
        id: Optional[str] = None,
        custom_fields_data: Optional[dict] = None,
    ) -> "SecurityIncident":
        if not title or not title.strip():
            raise ValueError("Title is required")
        if not description or not description.strip():
            raise ValueError("Description is required")
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            title=title.strip(),
            description=description.strip(),
            incident_type=incident_type,
            severity=severity,
            status=IncidentStatus.DETECTED,
            reported_by=reported_by,
            detected_at=detected_at,
            attack_vector=attack_vector,
            data_breach_scope=data_breach_scope,
            custom_fields_data=custom_fields_data or {},
        )

    def change_status(
        self, new_status: IncidentStatus, close_reason: Optional[str] = None
    ) -> None:
        if self.status == IncidentStatus.CLOSED:
            raise IncidentClosedError()

        valid_targets = VALID_STATUS_TRANSITIONS.get(self.status, [])
        if new_status not in valid_targets:
            raise InvalidStatusTransitionError(self.status.value, new_status.value)

        if new_status == IncidentStatus.CLOSED:
            # close_reason required unless coming from recovered (normal closure)
            if self.status != IncidentStatus.RECOVERED:
                if not close_reason or not close_reason.strip():
                    raise CloseReasonRequiredError()
                self.close_reason = close_reason.strip()
            elif close_reason:
                self.close_reason = close_reason.strip()
            self.closed_at = datetime.now(timezone.utc)

        self.status = new_status

    def change_severity(self, new_severity: IncidentSeverity) -> None:
        if self.status == IncidentStatus.CLOSED:
            raise IncidentClosedError()
        self.severity = new_severity

    def assign_to(self, user_id: str) -> None:
        if self.status == IncidentStatus.CLOSED:
            raise IncidentClosedError()
        self.assigned_to = user_id

    def update_details(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        attack_vector: Optional[str] = None,
        data_breach_scope: Optional[str] = None,
    ) -> None:
        if self.status == IncidentStatus.CLOSED:
            raise IncidentClosedError()
        if title is not None:
            if not title.strip():
                raise ValueError("Title cannot be empty")
            self.title = title.strip()
        if description is not None:
            if not description.strip():
                raise ValueError("Description cannot be empty")
            self.description = description.strip()
        if attack_vector is not None:
            self.attack_vector = attack_vector
        if data_breach_scope is not None:
            self.data_breach_scope = data_breach_scope


@dataclass
class IncidentTimeline:
    id: str
    incident_id: str
    event_type: TimelineEventType
    description: str
    actor_id: str
    created_at: Optional[datetime] = None
    metadata: Optional[dict] = None

    @classmethod
    def create(
        cls,
        incident_id: str,
        event_type: TimelineEventType,
        description: str,
        actor_id: str,
        metadata: Optional[dict] = None,
    ) -> "IncidentTimeline":
        return cls(
            id=str(ulid.new()),
            incident_id=incident_id,
            event_type=event_type,
            description=description,
            actor_id=actor_id,
            metadata=metadata,
        )


@dataclass
class PostMortem:
    id: str
    incident_id: str
    root_cause: str
    lessons_learned: str
    corrective_actions: str
    created_by: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        incident_id: str,
        root_cause: str,
        lessons_learned: str,
        corrective_actions: str,
        created_by: str,
    ) -> "PostMortem":
        if not root_cause or not root_cause.strip():
            raise ValueError("Root cause is required")
        if not lessons_learned or not lessons_learned.strip():
            raise ValueError("Lessons learned is required")
        if not corrective_actions or not corrective_actions.strip():
            raise ValueError("Corrective actions is required")
        return cls(
            id=str(ulid.new()),
            incident_id=incident_id,
            root_cause=root_cause.strip(),
            lessons_learned=lessons_learned.strip(),
            corrective_actions=corrective_actions.strip(),
            created_by=created_by,
        )


REPORT_DEADLINES: dict[ReportType, timedelta] = {
    ReportType.EARLY_WARNING_24H: timedelta(hours=24),
    ReportType.DETAILED_72H: timedelta(hours=72),
    ReportType.FINAL_30D: timedelta(days=30),
}


@dataclass
class RegulatoryReport:
    id: str
    incident_id: str
    report_type: ReportType
    status: ReportStatus
    deadline_at: datetime
    generated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    file_path: Optional[str] = None

    @classmethod
    def create_for_incident(
        cls, incident_id: str, detected_at: datetime
    ) -> list["RegulatoryReport"]:
        reports: list[RegulatoryReport] = []
        for report_type, delta in REPORT_DEADLINES.items():
            reports.append(
                cls(
                    id=str(ulid.new()),
                    incident_id=incident_id,
                    report_type=report_type,
                    status=ReportStatus.PENDING,
                    deadline_at=detected_at + delta,
                )
            )
        return reports

    def mark_generated(self, file_path: str) -> None:
        self.status = ReportStatus.GENERATED
        self.file_path = file_path
        self.generated_at = datetime.now(timezone.utc)

    def mark_submitted(self) -> None:
        if self.status == ReportStatus.PENDING:
            raise ReportNotGeneratedError(self.id)
        self.status = ReportStatus.SUBMITTED
        self.submitted_at = datetime.now(timezone.utc)
