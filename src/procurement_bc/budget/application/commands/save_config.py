import logging
from dataclasses import dataclass

from src.procurement_bc.budget.domain.entities import (
    CompanyProcurementConfig,
)
from src.procurement_bc.budget.domain.repository import (
    CompanyProcurementConfigRepositoryInterface,
)
from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)

logger = logging.getLogger(__name__)


@dataclass
class SaveProcurementConfigCommand(Command):
    company_id: str
    enforcement_mode: str
    approval_threshold_cents: int
    po_number_prefix: str
    fiscal_year_start_month: int
    currency: str
    auto_create_assets: bool
    performed_by: str = ""


class SaveProcurementConfigCommandHandler(
    CommandHandler[SaveProcurementConfigCommand],
):
    def __init__(
        self,
        config_repo: CompanyProcurementConfigRepositoryInterface,
    ):
        self.config_repo = config_repo

    def handle(
        self,
        command: SaveProcurementConfigCommand,
    ) -> None:
        if command.enforcement_mode not in (
            "warn",
            "strict",
        ):
            raise ValueError(
                "enforcement_mode must be 'warn' or 'strict'"
            )
        if command.approval_threshold_cents < 0:
            raise ValueError(
                "approval_threshold_cents must be >= 0"
            )
        if not 1 <= command.fiscal_year_start_month <= 12:
            raise ValueError(
                "fiscal_year_start_month must be 1-12"
            )
        prefix = command.po_number_prefix.strip()
        if not prefix or len(prefix) > 10:
            raise ValueError(
                "po_number_prefix must be 1-10 characters"
            )
        if len(command.currency) != 3:
            raise ValueError(
                "currency must be a 3-character code"
            )

        existing = self.config_repo.find_by_company_id(
            command.company_id,
        )
        if existing:
            existing.enforcement_mode = (
                command.enforcement_mode
            )
            existing.approval_threshold_cents = (
                command.approval_threshold_cents
            )
            existing.po_number_prefix = prefix
            existing.fiscal_year_start_month = (
                command.fiscal_year_start_month
            )
            existing.currency = command.currency
            existing.auto_create_assets = (
                command.auto_create_assets
            )
            self.config_repo.save(existing)
        else:
            config = CompanyProcurementConfig.create(
                company_id=command.company_id,
                enforcement_mode=command.enforcement_mode,
                approval_threshold_cents=(
                    command.approval_threshold_cents
                ),
                po_number_prefix=prefix,
                fiscal_year_start_month=(
                    command.fiscal_year_start_month
                ),
                currency=command.currency,
                auto_create_assets=command.auto_create_assets,
            )
            self.config_repo.save(config)

        logger.info(
            "Procurement config saved for company %s",
            command.company_id,
        )
