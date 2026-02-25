from unittest.mock import MagicMock

import pytest

from src.workflow_bc.template.application.commands.create_template import (
    ChecklistItemInput,
    CreateWorkflowTemplateCommand,
    CreateWorkflowTemplateCommandHandler,
    SubtypeInput,
)
from src.workflow_bc.template.domain.exceptions import DuplicateTemplateNameError


class TestCreateWorkflowTemplateCommandHandler:
    def test_create_success(self):
        repo = MagicMock()
        repo.find_by_name.return_value = None

        handler = CreateWorkflowTemplateCommandHandler(repo=repo)
        handler.handle(
            CreateWorkflowTemplateCommand(
                template_id="01TPL",
                company_id="01COMP",
                name="Incident",
                description="Report an incident",
                icon="alert-circle",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.name == "Incident"
        assert saved.company_id == "01COMP"

    def test_create_with_subtypes_and_items(self):
        repo = MagicMock()
        repo.find_by_name.return_value = None

        handler = CreateWorkflowTemplateCommandHandler(repo=repo)
        handler.handle(
            CreateWorkflowTemplateCommand(
                template_id="01TPL",
                company_id="01COMP",
                name="Repair",
                subtypes=[
                    SubtypeInput(name="Hardware", sort_order=0),
                    SubtypeInput(name="Software", sort_order=1),
                ],
                checklist_items=[
                    ChecklistItemInput(title="Diagnose", sort_order=0),
                    ChecklistItemInput(title="Fix", sort_order=1),
                ],
            )
        )

        saved = repo.save.call_args[0][0]
        assert len(saved.subtypes) == 2
        assert saved.subtypes[0].name == "Hardware"
        assert len(saved.checklist_items) == 2
        assert saved.checklist_items[1].title == "Fix"

    def test_create_duplicate_name_raises(self):
        repo = MagicMock()
        repo.find_by_name.return_value = MagicMock()

        handler = CreateWorkflowTemplateCommandHandler(repo=repo)
        with pytest.raises(DuplicateTemplateNameError):
            handler.handle(
                CreateWorkflowTemplateCommand(
                    template_id="01TPL",
                    company_id="01COMP",
                    name="Incident",
                )
            )
        repo.save.assert_not_called()
