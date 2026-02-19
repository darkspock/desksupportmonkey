import pytest

from src.procurement_bc.budget.domain.entities import (
    CompanyProcurementConfig,
    DepartmentBudget,
)


class TestDepartmentBudgetCreate:
    def test_creates_budget(self):
        budget = DepartmentBudget.create(
            company_id="comp1",
            department_id="dept1",
            fiscal_year=2026,
            allocated_amount_cents=500000,
        )
        assert budget.id is not None
        assert len(budget.id) == 26
        assert budget.allocated_amount_cents == 500000
        assert budget.currency == "USD"

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError, match="negative"):
            DepartmentBudget.create(
                company_id="comp1",
                department_id="dept1",
                fiscal_year=2026,
                allocated_amount_cents=-100,
            )

    def test_zero_amount_allowed(self):
        budget = DepartmentBudget.create(
            company_id="comp1",
            department_id="dept1",
            fiscal_year=2026,
            allocated_amount_cents=0,
        )
        assert budget.allocated_amount_cents == 0


class TestCompanyProcurementConfigCreate:
    def test_creates_with_defaults(self):
        config = CompanyProcurementConfig.create(
            company_id="comp1",
        )
        assert config.enforcement_mode == "warn"
        assert config.approval_threshold_cents == 0
        assert config.po_number_prefix == "PO"
        assert config.fiscal_year_start_month == 1
        assert config.currency == "USD"
        assert config.auto_create_assets is False

    def test_invalid_enforcement_mode_raises(self):
        with pytest.raises(ValueError, match="enforcement"):
            CompanyProcurementConfig.create(
                company_id="comp1",
                enforcement_mode="invalid",
            )

    def test_negative_threshold_raises(self):
        with pytest.raises(ValueError, match="negative"):
            CompanyProcurementConfig.create(
                company_id="comp1",
                approval_threshold_cents=-1,
            )

    def test_invalid_fiscal_month_raises(self):
        with pytest.raises(ValueError, match="1-12"):
            CompanyProcurementConfig.create(
                company_id="comp1",
                fiscal_year_start_month=13,
            )

    def test_fiscal_month_zero_raises(self):
        with pytest.raises(ValueError, match="1-12"):
            CompanyProcurementConfig.create(
                company_id="comp1",
                fiscal_year_start_month=0,
            )

    def test_defaults_factory(self):
        config = CompanyProcurementConfig.defaults(
            company_id="comp1",
        )
        assert config.company_id == "comp1"
        assert config.enforcement_mode == "warn"
        assert config.id == ""
