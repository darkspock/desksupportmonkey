from unittest.mock import MagicMock

import pytest

from src.workflow_bc.template.application.commands.delete_template import (
    DeleteWorkflowTemplateCommand,
    DeleteWorkflowTemplateCommandHandler,
)
from src.workflow_bc.template.domain.entities import WorkflowTemplate
from src.workflow_bc.template.domain.exceptions import (
    TemplateHasRequestsError,
    WorkflowTemplateNotFoundError,
)


class TestDeleteWorkflowTemplateCommandHandler:
    def test_delete_success(self):
        repo = MagicMock()
        template = WorkflowTemplate.create(company_id="01COMP", name="Test")
        repo.find_by_id.return_value = template
        repo.has_requests.return_value = False

        handler = DeleteWorkflowTemplateCommandHandler(repo=repo)
        handler.handle(
            DeleteWorkflowTemplateCommand(
                template_id=template.id,
                company_id="01COMP",
            )
        )

        repo.delete.assert_called_once_with(template.id)

    def test_delete_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = DeleteWorkflowTemplateCommandHandler(repo=repo)
        with pytest.raises(WorkflowTemplateNotFoundError):
            handler.handle(
                DeleteWorkflowTemplateCommand(
                    template_id="01MISSING",
                    company_id="01COMP",
                )
            )

    def test_delete_has_requests(self):
        repo = MagicMock()
        template = WorkflowTemplate.create(company_id="01COMP", name="Test")
        repo.find_by_id.return_value = template
        repo.has_requests.return_value = True

        handler = DeleteWorkflowTemplateCommandHandler(repo=repo)
        with pytest.raises(TemplateHasRequestsError):
            handler.handle(
                DeleteWorkflowTemplateCommand(
                    template_id=template.id,
                    company_id="01COMP",
                )
            )
        repo.delete.assert_not_called()
