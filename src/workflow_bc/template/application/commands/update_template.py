from dataclasses import dataclass, field
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.workflow_bc.template.domain.entities import (
    ChecklistItemDefinition,
    WorkflowSubtype,
)
from src.workflow_bc.template.domain.exceptions import (
    DuplicateTemplateNameError,
    WorkflowTemplateNotFoundError,
)
from src.workflow_bc.template.domain.repository import WorkflowTemplateRepositoryInterface
from src.workflow_bc.template.application.commands.create_template import (
    ChecklistItemInput,
    SubtypeInput,
)


@dataclass
class UpdateWorkflowTemplateCommand(Command):
    template_id: str
    company_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    require_all_complete: Optional[bool] = None
    sort_order: Optional[int] = None
    subtypes: Optional[list[SubtypeInput]] = None
    checklist_items: Optional[list[ChecklistItemInput]] = None


class UpdateWorkflowTemplateCommandHandler(
    CommandHandler[UpdateWorkflowTemplateCommand]
):
    def __init__(self, repo: WorkflowTemplateRepositoryInterface):
        self.repo = repo

    def handle(self, command: UpdateWorkflowTemplateCommand) -> None:
        template = self.repo.find_by_id(command.template_id, command.company_id)
        if not template:
            raise WorkflowTemplateNotFoundError(command.template_id)

        # Check name uniqueness if changing name
        if command.name is not None and command.name != template.name:
            existing = self.repo.find_by_name(command.company_id, command.name)
            if existing:
                raise DuplicateTemplateNameError(command.name)

        template.update(
            name=command.name,
            description=command.description,
            icon=command.icon,
            is_active=command.is_active,
            require_all_complete=command.require_all_complete,
            sort_order=command.sort_order,
        )

        if command.subtypes is not None:
            subtypes = [
                WorkflowSubtype.create(
                    template_id=template.id,
                    name=s.name,
                    description=s.description,
                    sort_order=s.sort_order,
                )
                for s in command.subtypes
            ]
            template.set_subtypes(subtypes)

        if command.checklist_items is not None:
            items = [
                ChecklistItemDefinition.create(
                    template_id=template.id,
                    title=ci.title,
                    description=ci.description,
                    assignee_role=ci.assignee_role,
                    sort_order=ci.sort_order,
                    is_required=ci.is_required,
                )
                for ci in command.checklist_items
            ]
            template.set_checklist_items(items)

        self.repo.save(template)
