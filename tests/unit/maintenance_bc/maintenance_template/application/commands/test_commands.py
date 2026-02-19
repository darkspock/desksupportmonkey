from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from src.maintenance_bc.maintenance_record.application.ports import (
    AssetSummary,
)
from src.maintenance_bc.maintenance_template.application.commands.apply_template_to_assets import (
    ApplyTemplateToAssetsCommand,
    ApplyTemplateToAssetsCommandHandler,
    MaintenanceTemplateNotFoundError,
)
from src.maintenance_bc.maintenance_template.application.commands.create_maintenance_template import (
    CreateMaintenanceTemplateCommand,
    CreateMaintenanceTemplateCommandHandler,
)
from src.maintenance_bc.maintenance_template.application.commands.deactivate_plan import (
    DeactivatePlanCommand,
    DeactivatePlanCommandHandler,
)
from src.maintenance_bc.maintenance_template.application.commands.delete_maintenance_template import (
    DeleteMaintenanceTemplateCommand,
    DeleteMaintenanceTemplateCommandHandler,
)
from src.maintenance_bc.maintenance_template.application.commands.update_maintenance_template import (
    UpdateMaintenanceTemplateCommand,
    UpdateMaintenanceTemplateCommandHandler,
)
from src.maintenance_bc.maintenance_record.domain.enums import (
    MaintenancePriority,
    RecurrenceFrequency,
)
from src.maintenance_bc.maintenance_template.domain.entities import (
    ChecklistItem,
    MaintenancePlan,
    MaintenanceTemplate,
)


def _template() -> MaintenanceTemplate:
    return MaintenanceTemplate.create(
        company_id="comp1",
        name="Quarterly HVAC",
        default_priority=MaintenancePriority.HIGH,
        recurrence_frequency=RecurrenceFrequency.QUARTERLY,
        recurrence_interval=1,
        checklist_items=[ChecklistItem.create("Inspect")],
    )


class TestTemplateCommands:
    def test_create_template(self):
        repo = MagicMock()
        handler = CreateMaintenanceTemplateCommandHandler(template_repo=repo)

        handler.handle(
            CreateMaintenanceTemplateCommand(
                template_id="t1",
                company_id="comp1",
                name="Monthly",
                default_priority="MEDIUM",
                recurrence_frequency="MONTHLY",
                checklist_items=[{"title": "Inspect"}],
            )
        )

        repo.save.assert_called_once()

    def test_update_template(self):
        repo = MagicMock()
        template = _template()
        repo.find_by_id.return_value = template
        handler = UpdateMaintenanceTemplateCommandHandler(template_repo=repo)

        handler.handle(
            UpdateMaintenanceTemplateCommand(
                template_id=template.id,
                company_id=template.company_id,
                name="Quarterly HVAC Updated",
                recurrence_interval=2,
            )
        )

        assert template.name == "Quarterly HVAC Updated"
        assert template.recurrence_interval == 2
        repo.save.assert_called_once_with(template)

    def test_delete_template_soft_deactivate(self):
        repo = MagicMock()
        template = _template()
        repo.find_by_id.return_value = template
        handler = DeleteMaintenanceTemplateCommandHandler(template_repo=repo)

        handler.handle(
            DeleteMaintenanceTemplateCommand(
                template_id=template.id,
                company_id=template.company_id,
            )
        )

        assert template.is_active is False
        repo.save.assert_called_once_with(template)


class TestApplyTemplateCommand:
    def test_apply_creates_plan_and_record(self):
        template_repo = MagicMock()
        plan_repo = MagicMock()
        record_repo = MagicMock()
        asset_lookup = MagicMock()

        template = _template()
        template_repo.find_by_id.return_value = template
        asset_lookup.list_by_company.return_value = [
            AssetSummary(id="asset1", type="laptop"),
        ]
        plan_repo.find_active_by_template_asset.return_value = None

        handler = ApplyTemplateToAssetsCommandHandler(
            template_repo=template_repo,
            plan_repo=plan_repo,
            record_repo=record_repo,
            asset_lookup=asset_lookup,
        )

        handler.handle(
            ApplyTemplateToAssetsCommand(
                template_id=template.id,
                company_id=template.company_id,
                asset_ids=["asset1"],
                first_due_at=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
            )
        )

        assert plan_repo.save.call_count == 1
        assert record_repo.save.call_count == 1

    def test_apply_raises_when_template_missing(self):
        template_repo = MagicMock()
        template_repo.find_by_id.return_value = None
        handler = ApplyTemplateToAssetsCommandHandler(
            template_repo=template_repo,
            plan_repo=MagicMock(),
            record_repo=MagicMock(),
            asset_lookup=MagicMock(),
        )

        with pytest.raises(MaintenanceTemplateNotFoundError):
            handler.handle(
                ApplyTemplateToAssetsCommand(
                    template_id="x",
                    company_id="comp1",
                )
            )

    def test_deactivate_plan(self):
        plan_repo = MagicMock()
        plan = MaintenancePlan.create(
            company_id="comp1",
            template_id="t1",
            asset_id="a1",
            next_due_at=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )
        plan_repo.find_by_id.return_value = plan
        handler = DeactivatePlanCommandHandler(plan_repo=plan_repo)

        handler.handle(
            DeactivatePlanCommand(
                plan_id=plan.id,
                company_id=plan.company_id,
            )
        )

        assert plan.is_active is False
        plan_repo.save.assert_called_once_with(plan)
