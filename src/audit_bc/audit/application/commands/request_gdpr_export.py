from dataclasses import dataclass, field
from typing import Optional

import ulid

from src.audit_bc.audit.domain.entities import GdprRequest
from src.audit_bc.audit.domain.enums import GdprRequestType
from src.audit_bc.audit.domain.exceptions import TargetUserNotFoundError
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class RequestGdprExportCommand(Command):
    company_id: str
    target_user_email: str
    requested_by: str
    request_id: str = field(default_factory=lambda: str(ulid.new()))


class RequestGdprExportHandler(
    CommandHandler[RequestGdprExportCommand]
):
    def __init__(
        self,
        audit_repo: AuditRepositoryInterface,
        user_repo: UserRepositoryInterface,
    ):
        self.audit_repo = audit_repo
        self.user_repo = user_repo

    def handle(self, command: RequestGdprExportCommand) -> None:
        user = self.user_repo.find_by_email(command.target_user_email)
        if user is None or user.company_id != command.company_id:
            raise TargetUserNotFoundError(
                f"User '{command.target_user_email}' not found"
            )

        request = GdprRequest.create(
            company_id=command.company_id,
            target_user_id=user.id,
            target_user_email=user.email,
            requested_by=command.requested_by,
            request_type=GdprRequestType.EXPORT,
            request_id=command.request_id,
        )
        self.audit_repo.save_gdpr_request(request)
