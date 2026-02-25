from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.workflow_bc.template.domain.exceptions import (
    TemplateHasRequestsError,
    WorkflowTemplateNotFoundError,
)
from src.workflow_bc.template.domain.repository import WorkflowTemplateRepositoryInterface


@dataclass
class DeleteWorkflowTemplateCommand(Command):
    template_id: str
    company_id: str


class DeleteWorkflowTemplateCommandHandler(
    CommandHandler[DeleteWorkflowTemplateCommand]
):
    def __init__(self, repo: WorkflowTemplateRepositoryInterface):
        self.repo = repo

    def handle(self, command: DeleteWorkflowTemplateCommand) -> None:
        template = self.repo.find_by_id(command.template_id, command.company_id)
        if not template:
            raise WorkflowTemplateNotFoundError(command.template_id)

        if self.repo.has_requests(command.template_id):
            raise TemplateHasRequestsError(command.template_id)

        self.repo.delete(command.template_id)
