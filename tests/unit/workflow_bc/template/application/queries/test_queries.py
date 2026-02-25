from unittest.mock import MagicMock

import pytest

from src.workflow_bc.template.application.queries.list_templates import (
    ListWorkflowTemplatesQuery,
    ListWorkflowTemplatesQueryHandler,
    WorkflowTemplateDto,
)
from src.workflow_bc.template.application.queries.get_template import (
    GetWorkflowTemplateQuery,
    GetWorkflowTemplateQueryHandler,
)
from src.workflow_bc.template.domain.entities import WorkflowTemplate
from src.workflow_bc.template.domain.exceptions import WorkflowTemplateNotFoundError


def _make_template(**overrides):
    defaults = dict(company_id="01COMP", name="Incident")
    defaults.update(overrides)
    return WorkflowTemplate.create(**defaults)


class TestListWorkflowTemplatesQueryHandler:
    def test_list_returns_templates(self):
        repo = MagicMock()
        t1 = _make_template(name="Incident")
        t2 = _make_template(name="Repair")
        repo.find_by_company.return_value = [t1, t2]

        handler = ListWorkflowTemplatesQueryHandler(repo=repo)
        result = handler.handle(
            ListWorkflowTemplatesQuery(company_id="01COMP")
        )

        assert len(result) == 2
        assert isinstance(result[0], WorkflowTemplateDto)
        assert result[0].name == "Incident"
        assert result[1].name == "Repair"

    def test_list_returns_empty(self):
        repo = MagicMock()
        repo.find_by_company.return_value = []

        handler = ListWorkflowTemplatesQueryHandler(repo=repo)
        result = handler.handle(
            ListWorkflowTemplatesQuery(company_id="01COMP")
        )

        assert result == []


class TestGetWorkflowTemplateQueryHandler:
    def test_get_success(self):
        repo = MagicMock()
        template = _make_template()
        repo.find_by_id.return_value = template

        handler = GetWorkflowTemplateQueryHandler(repo=repo)
        result = handler.handle(
            GetWorkflowTemplateQuery(
                template_id=template.id,
                company_id="01COMP",
            )
        )

        assert isinstance(result, WorkflowTemplateDto)
        assert result.name == "Incident"

    def test_get_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = GetWorkflowTemplateQueryHandler(repo=repo)
        with pytest.raises(WorkflowTemplateNotFoundError):
            handler.handle(
                GetWorkflowTemplateQuery(
                    template_id="01MISSING",
                    company_id="01COMP",
                )
            )
