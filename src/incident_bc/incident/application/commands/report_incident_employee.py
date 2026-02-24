from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.incident_bc.incident.domain.entities import (
    IncidentTimeline,
    RegulatoryReport,
    SecurityIncident,
)
from src.incident_bc.incident.domain.enums import (
    IncidentSeverity,
    IncidentType,
    TimelineEventType,
)
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class ReportIncidentCommand(Command):
    company_id: str
    title: str
    description: str
    incident_type: str
    reported_by: str
    id: Optional[str] = None


class ReportIncidentCommandHandler(CommandHandler[ReportIncidentCommand]):
    def __init__(
        self,
        incident_repo: IncidentRepositoryInterface,
        event_bus: Optional[Any] = None,
        db: Optional[Any] = None,
    ):
        self.incident_repo = incident_repo
        self.event_bus = event_bus
        self.db = db

    def handle(self, command: ReportIncidentCommand) -> None:
        incident_type = IncidentType(command.incident_type)
        now = datetime.now(timezone.utc)

        incident = SecurityIncident.create(
            company_id=command.company_id,
            title=command.title,
            description=command.description,
            incident_type=incident_type,
            severity=IncidentSeverity.P3,
            detected_at=now,
            reported_by=command.reported_by,
            id=command.id,
        )

        self.incident_repo.save(incident)

        timeline_entry = IncidentTimeline.create(
            incident_id=incident.id,
            event_type=TimelineEventType.INCIDENT_CREATED,
            description="Incident reported by employee",
            actor_id=command.reported_by,
            metadata={
                "incident_type": incident_type.value,
                "severity": IncidentSeverity.P3.value,
                "source": "employee_report",
            },
        )
        self.incident_repo.save_timeline(timeline_entry)

        # Auto-create 3 NIS2 regulatory reports with deadlines
        regulatory_reports = RegulatoryReport.create_for_incident(
            incident_id=incident.id,
            detected_at=incident.detected_at,
        )
        self.incident_repo.save_reports_batch(regulatory_reports)

        # Notify admins + technicians
        if self.event_bus and self.db:
            from src.incident_bc.incident.application.services.incident_event_factory import (
                IncidentEventFactory,
            )

            event = IncidentEventFactory.employee_reported(
                incident, actor_id=command.reported_by
            )
            self.event_bus.publish(event, self.db)
