from dataclasses import dataclass, field
from typing import Optional

import ulid

from src.audit_bc.audit.domain.entities import GdprRequest
from src.audit_bc.audit.domain.enums import GdprRequestType
from src.audit_bc.audit.domain.exceptions import (
    CannotAnonymizeSelfError,
    CannotAnonymizeSuperAdminError,
    TargetUserNotFoundError,
    UserAlreadyAnonymizedError,
)
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.auth_bc.company_user.domain.repository import CompanyUserRepositoryInterface
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class RequestGdprAnonymizeCommand(Command):
    company_id: str
    target_user_email: str
    requested_by: str
    reason: Optional[str] = None
    request_id: str = field(default_factory=lambda: str(ulid.new()))


class RequestGdprAnonymizeHandler(
    CommandHandler[RequestGdprAnonymizeCommand]
):
    def __init__(
        self,
        audit_repo: AuditRepositoryInterface,
        user_repo: UserRepositoryInterface,
        company_user_repo: Optional[CompanyUserRepositoryInterface] = None,
    ):
        self.audit_repo = audit_repo
        self.user_repo = user_repo
        self.company_user_repo = company_user_repo

    def handle(self, command: RequestGdprAnonymizeCommand) -> None:
        user = self.user_repo.find_by_email(command.target_user_email)
        if user is None or user.company_id != command.company_id:
            raise TargetUserNotFoundError(
                f"User '{command.target_user_email}' not found"
            )

        if user.role == UserRole.SUPER_ADMIN:
            raise CannotAnonymizeSuperAdminError(
                "Cannot anonymize a super admin user"
            )

        if user.id == command.requested_by:
            raise CannotAnonymizeSelfError(
                "Cannot anonymize your own account"
            )

        if user.is_anonymized:
            raise UserAlreadyAnonymizedError(
                f"User '{command.target_user_email}' is already anonymized"
            )

        # Deactivate membership in the target company
        if self.company_user_repo:
            membership = self.company_user_repo.find_by_user_and_company(
                user.id, command.company_id
            )
            if membership:
                membership.deactivate()
                self.company_user_repo.save(membership)

            # Only create anonymize request if no active memberships remain
            active_count = self.company_user_repo.count_active_memberships(user.id)
            if active_count > 0:
                # User still has active memberships in other companies — skip identity anonymization
                return

        request = GdprRequest.create(
            company_id=command.company_id,
            target_user_id=user.id,
            target_user_email=user.email,
            requested_by=command.requested_by,
            request_type=GdprRequestType.ANONYMIZE,
            reason=command.reason,
            request_id=command.request_id,
        )
        self.audit_repo.save_gdpr_request(request)
