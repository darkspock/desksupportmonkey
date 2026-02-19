from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from src.maintenance_bc.maintenance_record.domain.enums import (
    MaintenancePriority,
)
from src.maintenance_bc.maintenance_template.application.queries.get_maintenance_plan import (
    GetMaintenancePlanQuery,
    GetMaintenancePlanQueryHandler,
    MaintenancePlanNotFoundError,
)
from src.maintenance_bc.maintenance_template.application.queries.get_maintenance_template import (
    GetMaintenanceTemplateQuery,
    GetMaintenanceTemplateQueryHandler,
    MaintenanceTemplateNotFoundError,
)
from src.maintenance_bc.maintenance_template.application.queries.list_maintenance_plans import (
    ListMaintenancePlansQuery,
    ListMaintenancePlansQueryHandler,
)
from src.maintenance_bc.maintenance_template.application.queries.list_maintenance_templates import (
    ListMaintenanceTemplatesQuery,
    ListMaintenanceTemplatesQueryHandler,
)
from src.maintenance_bc.maintenance_template.domain.entities import (
    MaintenancePlan,
    MaintenanceTemplate,
)


def _template() -> MaintenanceTemplate:
    return MaintenanceTemplate.create(
        company_id="comp1",
        name="Monthly",
        default_priority=MaintenancePriority.MEDIUM,
    )


def _plan() -> MaintenancePlan:
    return MaintenancePlan.create(
        company_id="comp1",
        template_id="t1",
        asset_id="a1",
        next_due_at=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
    )


class TestTemplateQueries:
    def test_get_template(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _template()
        handler = GetMaintenanceTemplateQueryHandler(template_repo=repo)
        result = handler.handle(GetMaintenanceTemplateQuery(template_id="t1", company_id="comp1"))
        assert result.name == "Monthly"

    def test_get_template_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetMaintenanceTemplateQueryHandler(template_repo=repo)
        with pytest.raises(MaintenanceTemplateNotFoundError):
            handler.handle(GetMaintenanceTemplateQuery(template_id="x", company_id="comp1"))

    def test_list_templates(self):
        repo = MagicMock()
        repo.find_all.return_value = ([_template()], 1)
        handler = ListMaintenanceTemplatesQueryHandler(template_repo=repo)
        items, total = handler.handle(ListMaintenanceTemplatesQuery(company_id="comp1"))
        assert len(items) == 1
        assert total == 1


class TestPlanQueries:
    def test_get_plan(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _plan()
        handler = GetMaintenancePlanQueryHandler(plan_repo=repo)
        result = handler.handle(GetMaintenancePlanQuery(plan_id="p1", company_id="comp1"))
        assert result.asset_id == "a1"

    def test_get_plan_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetMaintenancePlanQueryHandler(plan_repo=repo)
        with pytest.raises(MaintenancePlanNotFoundError):
            handler.handle(GetMaintenancePlanQuery(plan_id="x", company_id="comp1"))

    def test_list_plans(self):
        repo = MagicMock()
        repo.find_all.return_value = ([_plan()], 1)
        handler = ListMaintenancePlansQueryHandler(plan_repo=repo)
        items, total = handler.handle(ListMaintenancePlansQuery(company_id="comp1"))
        assert len(items) == 1
        assert total == 1
