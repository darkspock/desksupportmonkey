from dataclasses import dataclass, field
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.workflow_bc.template.domain.entities import (
    ChecklistItemDefinition,
    WorkflowSubtype,
    WorkflowTemplate,
)
from src.workflow_bc.template.domain.exceptions import DuplicateTemplateNameError
from src.workflow_bc.template.domain.repository import WorkflowTemplateRepositoryInterface


@dataclass
class SubtypeInput:
    name: str
    description: Optional[str] = None
    sort_order: int = 0


@dataclass
class ChecklistItemInput:
    title: str
    description: Optional[str] = None
    assignee_role: Optional[str] = None
    sort_order: int = 0
    is_required: bool = True


@dataclass
class CreateWorkflowTemplateCommand(Command):
    template_id: str
    company_id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    require_all_complete: bool = False
    sort_order: int = 0
    subtypes: list[SubtypeInput] = field(default_factory=list)
    checklist_items: list[ChecklistItemInput] = field(default_factory=list)


class CreateWorkflowTemplateCommandHandler(
    CommandHandler[CreateWorkflowTemplateCommand]
):
    def __init__(self, repo: WorkflowTemplateRepositoryInterface):
        self.repo = repo

    def handle(self, command: CreateWorkflowTemplateCommand) -> None:
        existing = self.repo.find_by_name(command.company_id, command.name)
        if existing:
            raise DuplicateTemplateNameError(command.name)

        template = WorkflowTemplate.create(
            company_id=command.company_id,
            name=command.name,
            description=command.description,
            icon=command.icon,
            require_all_complete=command.require_all_complete,
            sort_order=command.sort_order,
            id=command.template_id,
        )

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
