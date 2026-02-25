from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.workflow_bc.checklist.domain.entities import RequestChecklistItem
from src.workflow_bc.checklist.domain.repository import ChecklistItemRepositoryInterface
from src.workflow_bc.template.domain.repository import WorkflowTemplateRepositoryInterface


@dataclass
class GenerateChecklistCommand(Command):
    request_id: str
    template_id: str
    company_id: str


class GenerateChecklistCommandHandler(CommandHandler[GenerateChecklistCommand]):
    def __init__(
        self,
        template_repo: WorkflowTemplateRepositoryInterface,
        checklist_repo: ChecklistItemRepositoryInterface,
    ):
        self.template_repo = template_repo
        self.checklist_repo = checklist_repo

    def handle(self, command: GenerateChecklistCommand) -> None:
        template = self.template_repo.find_by_id(
            command.template_id, command.company_id
        )
        if not template or not template.checklist_items:
            return

        items = [
            RequestChecklistItem.create(
                request_id=command.request_id,
                title=defn.title,
                require_all_complete=template.require_all_complete,
                description=defn.description,
                is_required=defn.is_required,
                sort_order=defn.sort_order,
            )
            for defn in template.checklist_items
        ]
        self.checklist_repo.save_all(items)
