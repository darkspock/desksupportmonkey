from dataclasses import dataclass

from src.audit_bc.audit.domain.exceptions import GdprRequestNotFoundError
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class CancelGdprRequestCommand(Command):
    request_id: str
    company_id: str


class CancelGdprRequestHandler(
    CommandHandler[CancelGdprRequestCommand]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(self, command: CancelGdprRequestCommand) -> None:
        request = self.repo.find_gdpr_request_by_id(
            command.request_id, company_id=command.company_id
        )
        if request is None:
            raise GdprRequestNotFoundError(
                f"GDPR request {command.request_id} not found"
            )

        request.cancel()
        self.repo.save_gdpr_request(request)
