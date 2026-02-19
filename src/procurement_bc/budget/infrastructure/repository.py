from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.procurement_bc.budget.domain.entities import (
    CompanyProcurementConfig,
    DepartmentBudget,
)
from src.procurement_bc.budget.domain.repository import (
    CompanyProcurementConfigRepositoryInterface,
    DepartmentBudgetRepositoryInterface,
)
from src.procurement_bc.budget.infrastructure.models import (
    CompanyProcurementConfigModel,
    DepartmentBudgetModel,
)


class DepartmentBudgetRepository(
    DepartmentBudgetRepositoryInterface,
):
    def __init__(self, session: Session):
        self.session = session

    def save(
        self, budget: DepartmentBudget,
    ) -> DepartmentBudget:
        existing = self.session.execute(
            select(DepartmentBudgetModel).where(
                DepartmentBudgetModel.department_id
                == budget.department_id,
                DepartmentBudgetModel.fiscal_year
                == budget.fiscal_year,
                DepartmentBudgetModel.company_id
                == budget.company_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.allocated_amount_cents = (
                budget.allocated_amount_cents
            )
            existing.currency = budget.currency
        else:
            model = DepartmentBudgetModel(
                id=budget.id,
                company_id=budget.company_id,
                department_id=budget.department_id,
                fiscal_year=budget.fiscal_year,
                allocated_amount_cents=(
                    budget.allocated_amount_cents
                ),
                currency=budget.currency,
            )
            self.session.add(model)

        self.session.flush()
        return budget

    def find_by_department_year(
        self,
        department_id: str,
        fiscal_year: int,
        company_id: str,
    ) -> Optional[DepartmentBudget]:
        model = self.session.execute(
            select(DepartmentBudgetModel).where(
                DepartmentBudgetModel.department_id
                == department_id,
                DepartmentBudgetModel.fiscal_year
                == fiscal_year,
                DepartmentBudgetModel.company_id
                == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all_by_company_year(
        self, company_id: str, fiscal_year: int,
    ) -> list[DepartmentBudget]:
        models = (
            self.session.execute(
                select(DepartmentBudgetModel)
                .where(
                    DepartmentBudgetModel.company_id
                    == company_id,
                    DepartmentBudgetModel.fiscal_year
                    == fiscal_year,
                )
                .order_by(
                    DepartmentBudgetModel.department_id,
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    @staticmethod
    def _to_entity(
        model: DepartmentBudgetModel,
    ) -> DepartmentBudget:
        return DepartmentBudget(
            id=model.id,
            company_id=model.company_id,
            department_id=model.department_id,
            fiscal_year=model.fiscal_year,
            allocated_amount_cents=(
                model.allocated_amount_cents
            ),
            currency=model.currency,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class CompanyProcurementConfigRepository(
    CompanyProcurementConfigRepositoryInterface,
):
    def __init__(self, session: Session):
        self.session = session

    def save(
        self, config: CompanyProcurementConfig,
    ) -> CompanyProcurementConfig:
        existing = self.session.execute(
            select(CompanyProcurementConfigModel).where(
                CompanyProcurementConfigModel.company_id
                == config.company_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.enforcement_mode = (
                config.enforcement_mode
            )
            existing.approval_threshold_cents = (
                config.approval_threshold_cents
            )
            existing.po_number_prefix = (
                config.po_number_prefix
            )
            existing.fiscal_year_start_month = (
                config.fiscal_year_start_month
            )
            existing.currency = config.currency
            existing.auto_create_assets = (
                config.auto_create_assets
            )
        else:
            model = CompanyProcurementConfigModel(
                id=config.id,
                company_id=config.company_id,
                enforcement_mode=config.enforcement_mode,
                approval_threshold_cents=(
                    config.approval_threshold_cents
                ),
                po_number_prefix=config.po_number_prefix,
                fiscal_year_start_month=(
                    config.fiscal_year_start_month
                ),
                currency=config.currency,
                auto_create_assets=config.auto_create_assets,
            )
            self.session.add(model)

        self.session.flush()
        return config

    def find_by_company_id(
        self, company_id: str,
    ) -> Optional[CompanyProcurementConfig]:
        model = self.session.execute(
            select(CompanyProcurementConfigModel).where(
                CompanyProcurementConfigModel.company_id
                == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(
        model: CompanyProcurementConfigModel,
    ) -> CompanyProcurementConfig:
        return CompanyProcurementConfig(
            id=model.id,
            company_id=model.company_id,
            enforcement_mode=model.enforcement_mode,
            approval_threshold_cents=(
                model.approval_threshold_cents
            ),
            po_number_prefix=model.po_number_prefix,
            fiscal_year_start_month=(
                model.fiscal_year_start_month
            ),
            currency=model.currency,
            auto_create_assets=model.auto_create_assets,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
