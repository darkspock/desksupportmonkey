import logging
from dataclasses import dataclass

from src.procurement_bc.budget.domain.entities import (
    DepartmentBudget,
)
from src.procurement_bc.budget.domain.repository import (
    DepartmentBudgetRepositoryInterface,
)
from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)

logger = logging.getLogger(__name__)


@dataclass
class SetDepartmentBudgetCommand(Command):
    company_id: str
    department_id: str
    fiscal_year: int
    allocated_amount_cents: int
    currency: str = "USD"
    performed_by: str = ""


class SetDepartmentBudgetCommandHandler(
    CommandHandler[SetDepartmentBudgetCommand],
):
    def __init__(
        self,
        budget_repo: DepartmentBudgetRepositoryInterface,
    ):
        self.budget_repo = budget_repo

    def handle(
        self,
        command: SetDepartmentBudgetCommand,
    ) -> None:
        if command.allocated_amount_cents < 0:
            raise ValueError(
                "Budget amount cannot be negative"
            )

        existing = self.budget_repo.find_by_department_year(
            command.department_id,
            command.fiscal_year,
            command.company_id,
        )

        if existing:
            existing.allocated_amount_cents = (
                command.allocated_amount_cents
            )
            existing.currency = command.currency
            self.budget_repo.save(existing)
        else:
            budget = DepartmentBudget.create(
                company_id=command.company_id,
                department_id=command.department_id,
                fiscal_year=command.fiscal_year,
                allocated_amount_cents=(
                    command.allocated_amount_cents
                ),
                currency=command.currency,
            )
            self.budget_repo.save(budget)

        logger.info(
            "Budget set for dept %s FY %d: %d cents",
            command.department_id,
            command.fiscal_year,
            command.allocated_amount_cents,
        )
