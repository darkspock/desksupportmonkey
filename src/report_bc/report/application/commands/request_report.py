from dataclasses import dataclass
from typing import Any, Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.report_bc.report.domain.entities import Report
from src.report_bc.report.domain.repository import ReportRepositoryInterface


@dataclass
class RequestReportCommand(Command):
    company_id: str
    requested_by: str
    type: str
    parameters: Optional[dict[str, Any]] = None
    id: Optional[str] = None


class RequestReportCommandHandler(CommandHandler[RequestReportCommand]):
    def __init__(self, report_repo: ReportRepositoryInterface):
        self.report_repo = report_repo

    def handle(self, command: RequestReportCommand) -> None:
        report = Report.create(
            company_id=command.company_id,
            requested_by=command.requested_by,
            type=command.type,
            parameters=command.parameters,
            id=command.id,
        )
        self.report_repo.save(report)

        from core.tasks.reports import generate_report
        generate_report.delay(report.id)
