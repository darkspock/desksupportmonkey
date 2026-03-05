import pytest

from src.workflow_bc.template.domain.entities import (
    ChecklistItemDefinition,
    WorkflowSubtype,
    WorkflowTemplate,
)


class TestWorkflowTemplate:
    def test_create_success(self):
        t = WorkflowTemplate.create(
            company_id="01COMP",
            name="Incident",
            description="Report an incident",
            icon="circle-alert",
        )
        assert t.name == "Incident"
        assert t.company_id == "01COMP"
        assert t.is_active is True
        assert t.require_all_complete is False
        assert t.created_at is not None

    def test_create_trims_name(self):
        t = WorkflowTemplate.create(company_id="01COMP", name="  Incident  ")
        assert t.name == "Incident"

    def test_create_empty_name_raises(self):
        with pytest.raises(ValueError, match="required"):
            WorkflowTemplate.create(company_id="01COMP", name="")

    def test_update(self):
        t = WorkflowTemplate.create(company_id="01COMP", name="Old")
        t.update(name="New", is_active=False, require_all_complete=True)
        assert t.name == "New"
        assert t.is_active is False
        assert t.require_all_complete is True

    def test_update_empty_name_raises(self):
        t = WorkflowTemplate.create(company_id="01COMP", name="Test")
        with pytest.raises(ValueError, match="required"):
            t.update(name="   ")

    def test_set_subtypes(self):
        t = WorkflowTemplate.create(company_id="01COMP", name="Test")
        s = WorkflowSubtype.create(template_id=t.id, name="Hardware")
        t.set_subtypes([s])
        assert len(t.subtypes) == 1
        assert t.subtypes[0].name == "Hardware"

    def test_set_checklist_items(self):
        t = WorkflowTemplate.create(company_id="01COMP", name="Test")
        ci = ChecklistItemDefinition.create(
            template_id=t.id, title="Disable email"
        )
        t.set_checklist_items([ci])
        assert len(t.checklist_items) == 1
        assert t.checklist_items[0].title == "Disable email"


class TestWorkflowSubtype:
    def test_create_success(self):
        s = WorkflowSubtype.create(template_id="01TPL", name="Hardware")
        assert s.name == "Hardware"
        assert s.template_id == "01TPL"

    def test_create_empty_name_raises(self):
        with pytest.raises(ValueError, match="required"):
            WorkflowSubtype.create(template_id="01TPL", name="")


class TestChecklistItemDefinition:
    def test_create_success(self):
        ci = ChecklistItemDefinition.create(
            template_id="01TPL",
            title="Disable email",
            description="Disable all corporate email",
            assignee_role="admin",
            is_required=True,
        )
        assert ci.title == "Disable email"
        assert ci.is_required is True
        assert ci.assignee_role == "admin"

    def test_create_empty_title_raises(self):
        with pytest.raises(ValueError, match="required"):
            ChecklistItemDefinition.create(template_id="01TPL", title="")
