from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.incident_bc.incident.domain.entities import IncidentTimeline
from src.incident_bc.incident.domain.enums import TimelineEventType
from src.incident_bc.incident.domain.exceptions import (
    IncidentNotFoundError,
    ReportNotFoundError,
)
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class SubmitReportCommand(Command):
    incident_id: str
    report_id: str
    company_id: str
    actor_id: str


class SubmitReportCommandHandler(CommandHandler[SubmitReportCommand]):
    def __init__(
        self,
        incident_repo: IncidentRepositoryInterface,
    ):
        self.incident_repo = incident_repo

    def handle(self, command: SubmitReportCommand) -> None:
        incident = self.incident_repo.find_by_id(
            command.incident_id, command.company_id
        )
        if not incident:
            raise IncidentNotFoundError(command.incident_id)

        report = self.incident_repo.find_report_by_id(
            command.report_id, command.incident_id
        )
        if not report:
            raise ReportNotFoundError(command.report_id)

        # mark_submitted validates that report is generated (not pending)
        report.mark_submitted()
        self.incident_repo.update_report(report)

        timeline_entry = IncidentTimeline.create(
            incident_id=command.incident_id,
            event_type=TimelineEventType.REPORT_SUBMITTED,
            description=f"Submitted {report.report_type.value.replace('_', ' ')} report",
            actor_id=command.actor_id,
            metadata={"report_id": report.id, "report_type": report.report_type.value},
        )
        self.incident_repo.save_timeline(timeline_entry)
