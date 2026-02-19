from datetime import UTC, datetime

import pytest

from src.maintenance_bc.maintenance_record.domain.enums import (
    MaintenancePriority,
    RecurrenceFrequency,
)
from src.maintenance_bc.maintenance_template.domain.entities import (
    ChecklistItem,
    MaintenancePlan,
    MaintenanceTemplate,
)


class TestChecklistItem:

    def test_create_item(self):
        item = ChecklistItem.create(
            title="Inspect cable",
            description="Look for wear",
            is_required=True,
        )
        assert item.title == "Inspect cable"
        assert item.description == "Look for wear"
        assert item.is_required is True

    def test_create_requires_title(self):
        with pytest.raises(ValueError, match="title"):
            ChecklistItem.create(title="")


class TestMaintenanceTemplate:

    def test_create_template(self):
        template = MaintenanceTemplate.create(
            company_id="c1",
            name="Quarterly HVAC",
            default_priority=MaintenancePriority.HIGH,
            recurrence_frequency=RecurrenceFrequency.QUARTERLY,
            recurrence_interval=1,
            checklist_items=[ChecklistItem.create("Inspect fan")],
        )
        assert template.company_id == "c1"
        assert template.default_priority == MaintenancePriority.HIGH
        assert template.recurrence_frequency == RecurrenceFrequency.QUARTERLY
        assert template.recurrence_interval == 1
        assert len(template.checklist_items) == 1
        assert template.is_active is True

    def test_create_requires_name(self):
        with pytest.raises(ValueError, match="name"):
            MaintenanceTemplate.create(
                company_id="c1",
                name="",
            )

    def test_create_validates_interval(self):
        with pytest.raises(ValueError, match=">= 1"):
            MaintenanceTemplate.create(
                company_id="c1",
                name="Monthly",
                recurrence_interval=0,
            )

    def test_update_fields(self):
        template = MaintenanceTemplate.create(
            company_id="c1",
            name="Monthly",
            recurrence_frequency=RecurrenceFrequency.MONTHLY,
        )
        template.update(
            name="Monthly Updated",
            description="New desc",
            default_priority=MaintenancePriority.CRITICAL,
            recurrence_interval=2,
            asset_type_filter="laptop",
            checklist_items=[ChecklistItem.create("Inspect keyboard")],
        )

        assert template.name == "Monthly Updated"
        assert template.description == "New desc"
        assert template.default_priority == MaintenancePriority.CRITICAL
        assert template.recurrence_interval == 2
        assert template.asset_type_filter == "laptop"
        assert len(template.checklist_items) == 1

    def test_update_rejects_empty_name(self):
        template = MaintenanceTemplate.create(
            company_id="c1",
            name="Template",
        )
        with pytest.raises(ValueError, match="cannot be empty"):
            template.update(name="  ")

    def test_update_rejects_invalid_interval(self):
        template = MaintenanceTemplate.create(
            company_id="c1",
            name="Template",
        )
        with pytest.raises(ValueError, match=">= 1"):
            template.update(recurrence_interval=0)

    def test_deactivate_template(self):
        template = MaintenanceTemplate.create(
            company_id="c1",
            name="Template",
        )
        template.deactivate()
        assert template.is_active is False


class TestMaintenancePlan:

    def test_create_plan(self):
        next_due = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)
        plan = MaintenancePlan.create(
            company_id="c1",
            template_id="t1",
            asset_id="a1",
            next_due_at=next_due,
        )
        assert plan.company_id == "c1"
        assert plan.template_id == "t1"
        assert plan.asset_id == "a1"
        assert plan.next_due_at == next_due
        assert plan.is_active is True

    def test_update_next_due(self):
        plan = MaintenancePlan.create(
            company_id="c1",
            template_id="t1",
            asset_id="a1",
            next_due_at=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )
        next_due = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)
        generated = datetime(2026, 4, 1, 8, 5, tzinfo=UTC)

        plan.update_next_due(next_due_at=next_due, last_generated_at=generated)

        assert plan.next_due_at == next_due
        assert plan.last_generated_at == generated

    def test_deactivate_plan(self):
        plan = MaintenancePlan.create(
            company_id="c1",
            template_id="t1",
            asset_id="a1",
            next_due_at=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )
        plan.deactivate()
        assert plan.is_active is False
