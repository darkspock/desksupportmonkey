from unittest.mock import MagicMock

import pytest

from src.workflow_bc.template.application.commands.update_template import (
    UpdateWorkflowTemplateCommand,
    UpdateWorkflowTemplateCommandHandler,
)
from src.workflow_bc.template.domain.entities import WorkflowTemplate
from src.workflow_bc.template.domain.exceptions import (
    DuplicateTemplateNameError,
    WorkflowTemplateNotFoundError,
)


def _make_template(**overrides):
    defaults = dict(company_id="01COMP", name="Incident")
    defaults.update(overrides)
    return WorkflowTemplate.create(**defaults)


class TestUpdateWorkflowTemplateCommandHandler:
    def test_update_success(self):
        repo = MagicMock()
        template = _make_template()
        repo.find_by_id.return_value = template
        repo.find_by_name.return_value = None

        handler = UpdateWorkflowTemplateCommandHandler(repo=repo)
        handler.handle(
            UpdateWorkflowTemplateCommand(
                template_id=template.id,
                company_id="01COMP",
                name="Updated",
                is_active=False,
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.name == "Updated"
        assert saved.is_active is False

    def test_update_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = UpdateWorkflowTemplateCommandHandler(repo=repo)
        with pytest.raises(WorkflowTemplateNotFoundError):
            handler.handle(
                UpdateWorkflowTemplateCommand(
                    template_id="01MISSING",
                    company_id="01COMP",
                    name="Test",
                )
            )

    def test_update_duplicate_name(self):
        repo = MagicMock()
        template = _make_template()
        repo.find_by_id.return_value = template
        repo.find_by_name.return_value = MagicMock()  # Another template exists

        handler = UpdateWorkflowTemplateCommandHandler(repo=repo)
        with pytest.raises(DuplicateTemplateNameError):
            handler.handle(
                UpdateWorkflowTemplateCommand(
                    template_id=template.id,
                    company_id="01COMP",
                    name="Existing Name",
                )
            )
        repo.save.assert_not_called()
