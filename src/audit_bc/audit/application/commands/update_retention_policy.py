from dataclasses import dataclass

from src.audit_bc.audit.domain.entities import (
    VALID_RETENTION_MONTHS,
    RetentionPolicy,
)
from src.audit_bc.audit.domain.exceptions import (
    InvalidRetentionPeriodError,
)
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class UpdateRetentionPolicyCommand(Command):
    company_id: str
    retention_months: int
    updated_by: str


class UpdateRetentionPolicyHandler(
    CommandHandler[UpdateRetentionPolicyCommand]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(self, command: UpdateRetentionPolicyCommand) -> None:
        if command.retention_months not in VALID_RETENTION_MONTHS:
            raise InvalidRetentionPeriodError(
                f"Invalid retention period: {command.retention_months}. "
                f"Valid values: {VALID_RETENTION_MONTHS}"
            )

        existing = self.repo.find_retention_policy(command.company_id)
        if existing:
            existing.retention_months = command.retention_months
            existing.updated_by = command.updated_by
            from datetime import datetime, timezone
            existing.updated_at = datetime.now(timezone.utc)
            self.repo.save_retention_policy(existing)
        else:
            policy = RetentionPolicy.create(
                company_id=command.company_id,
                retention_months=command.retention_months,
                updated_by=command.updated_by,
            )
            self.repo.save_retention_policy(policy)
