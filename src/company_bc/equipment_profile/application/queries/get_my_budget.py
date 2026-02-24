from dataclasses import dataclass
from typing import Optional

from src.company_bc.equipment_profile.domain.repository import (
    EquipmentProfileRepositoryInterface,
)
from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)


@dataclass
class BudgetItemReadModel:
    asset_type: str
    budget_cents: int


@dataclass
class MyBudgetReadModel:
    items: list[BudgetItemReadModel]


@dataclass
class GetMyBudgetQuery(Query):
    company_id: Optional[str]
    department_id: Optional[str]
    employee_role_id: Optional[str]


class GetMyBudgetQueryHandler(
    QueryHandler[GetMyBudgetQuery, MyBudgetReadModel],
):
    def __init__(
        self,
        profile_repo: EquipmentProfileRepositoryInterface,
    ):
        self.profile_repo = profile_repo

    def handle(
        self, query: GetMyBudgetQuery,
    ) -> MyBudgetReadModel:
        if (
            not query.company_id
            or not query.department_id
            or not query.employee_role_id
        ):
            return MyBudgetReadModel(items=[])

        profile = self.profile_repo.find_active(
            company_id=query.company_id,
            department_id=query.department_id,
            employee_role_id=query.employee_role_id,
        )
        if not profile:
            return MyBudgetReadModel(items=[])

        return MyBudgetReadModel(
            items=[
                BudgetItemReadModel(
                    asset_type=item.asset_type,
                    budget_cents=item.budget_cents,
                )
                for item in profile.items
                if item.budget_cents is not None
            ],
        )
