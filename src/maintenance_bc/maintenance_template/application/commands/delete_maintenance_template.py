from dataclasses import dataclass

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.maintenance_bc.maintenance_template.domain.repository import (
    MaintenanceTemplateRepositoryInterface,
)


class MaintenanceTemplateNotFoundError(Exception):
    pass


@dataclass
class DeleteMaintenanceTemplateCommand(Command):
    template_id: str
    company_id: str


class DeleteMaintenanceTemplateCommandHandler(
    CommandHandler[DeleteMaintenanceTemplateCommand],
):
    def __init__(
        self,
        template_repo: MaintenanceTemplateRepositoryInterface,
    ):
        self.template_repo = template_repo

    def handle(
        self,
        command: DeleteMaintenanceTemplateCommand,
    ) -> None:
        template = self.template_repo.find_by_id(
            command.template_id,
            command.company_id,
        )
        if not template:
            raise MaintenanceTemplateNotFoundError("Maintenance template not found")

        template.deactivate()
        self.template_repo.save(template)
