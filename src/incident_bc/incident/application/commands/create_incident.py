from dataclasses import dataclass
from datetime import datetime
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
class CreateIncidentCommand(Command):
    company_id: str
    title: str
    description: str
    incident_type: str
    severity: str
    detected_at: datetime
    reported_by: str
    attack_vector: Optional[str] = None
    data_breach_scope: Optional[str] = None
    id: Optional[str] = None
    custom_fields_data: Optional[dict] = None


class CreateIncidentCommandHandler(CommandHandler[CreateIncidentCommand]):
    def __init__(
        self,
        incident_repo: IncidentRepositoryInterface,
        event_bus: Optional[Any] = None,
        db: Optional[Any] = None,
    ):
        self.incident_repo = incident_repo
        self.event_bus = event_bus
        self.db = db

    def handle(self, command: CreateIncidentCommand) -> None:
        incident_type = IncidentType(command.incident_type)
        severity = IncidentSeverity(command.severity)

        incident = SecurityIncident.create(
            company_id=command.company_id,
            title=command.title,
            description=command.description,
            incident_type=incident_type,
            severity=severity,
            detected_at=command.detected_at,
            reported_by=command.reported_by,
            attack_vector=command.attack_vector,
            data_breach_scope=command.data_breach_scope,
            id=command.id,
            custom_fields_data=command.custom_fields_data,
        )

        self.incident_repo.save(incident)

        timeline_entry = IncidentTimeline.create(
            incident_id=incident.id,
            event_type=TimelineEventType.INCIDENT_CREATED,
            description="Incident created",
            actor_id=command.reported_by,
            metadata={
                "incident_type": incident_type.value,
                "severity": severity.value,
            },
        )
        self.incident_repo.save_timeline(timeline_entry)

        # Auto-create 3 NIS2 regulatory reports with deadlines
        regulatory_reports = RegulatoryReport.create_for_incident(
            incident_id=incident.id,
            detected_at=incident.detected_at,
        )
        self.incident_repo.save_reports_batch(regulatory_reports)

        if self.event_bus and self.db:
            from src.incident_bc.incident.application.services.incident_event_factory import (
                IncidentEventFactory,
            )

            event = IncidentEventFactory.incident_created(
                incident, actor_id=command.reported_by
            )
            self.event_bus.publish(event, self.db)
