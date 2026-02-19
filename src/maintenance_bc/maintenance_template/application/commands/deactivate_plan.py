from dataclasses import dataclass

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.maintenance_bc.maintenance_template.domain.repository import (
    MaintenancePlanRepositoryInterface,
)


class MaintenancePlanNotFoundError(Exception):
    pass


@dataclass
class DeactivatePlanCommand(Command):
    plan_id: str
    company_id: str


class DeactivatePlanCommandHandler(
    CommandHandler[DeactivatePlanCommand],
):
    def __init__(
        self,
        plan_repo: MaintenancePlanRepositoryInterface,
    ):
        self.plan_repo = plan_repo

    def handle(
        self,
        command: DeactivatePlanCommand,
    ) -> None:
        plan = self.plan_repo.find_by_id(
            command.plan_id,
            command.company_id,
        )
        if not plan:
            raise MaintenancePlanNotFoundError("Maintenance plan not found")

        plan.deactivate()
        self.plan_repo.save(plan)
