import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from adapters.http.api.auth.dependencies import (
    require_role,
)
from adapters.http.api.budgets.dependencies import (
    get_budget_checker,
    get_budget_repo,
)
from adapters.http.api.budgets.schemas import (
    BudgetDepartmentItem,
    BudgetResponse,
    BudgetSetRequest,
    BudgetSummaryResponse,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.procurement_bc.budget.application.commands.set_budget import (  # noqa: E501
    SetDepartmentBudgetCommand,
    SetDepartmentBudgetCommandHandler,
)
from src.procurement_bc.budget.application.queries.get_budget import (  # noqa: E501
    GetDepartmentBudgetQuery,
    GetDepartmentBudgetQueryHandler,
)
from src.procurement_bc.budget.application.queries.get_summary import (  # noqa: E501
    GetBudgetSummaryQuery,
    GetBudgetSummaryQueryHandler,
)
from src.procurement_bc.budget.application.services.budget_checker import (  # noqa: E501
    BudgetChecker,
)
from src.procurement_bc.budget.infrastructure.repository import (
    DepartmentBudgetRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1", tags=["budgets"],
)


@router.put("/departments/{department_id}/budget")
def set_department_budget(
    department_id: str,
    body: BudgetSetRequest,
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    budget_repo: DepartmentBudgetRepository = Depends(
        get_budget_repo,
    ),
    budget_checker: BudgetChecker = Depends(
        get_budget_checker,
    ),
):
    fiscal_year = body.fiscal_year
    if fiscal_year is None:
        config = (
            budget_checker.config_repo.find_by_company_id(
                current_user.company_id,
            )
        )
        start_month = (
            config.fiscal_year_start_month if config
            else 1
        )
        fiscal_year = BudgetChecker.get_fiscal_year(
            start_month,
        )

    handler = SetDepartmentBudgetCommandHandler(
        budget_repo=budget_repo,
    )
    try:
        handler.handle(
            SetDepartmentBudgetCommand(
                company_id=current_user.company_id,
                department_id=department_id,
                fiscal_year=fiscal_year,
                allocated_amount_cents=(
                    body.allocated_amount_cents
                ),
                performed_by=current_user.id,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(e),
        )

    query_handler = GetDepartmentBudgetQueryHandler(
        budget_repo=budget_repo,
        budget_checker=budget_checker,
    )
    result = query_handler.handle(
        GetDepartmentBudgetQuery(
            company_id=current_user.company_id,
            department_id=department_id,
            fiscal_year=fiscal_year,
        )
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found after save",
        )

    return {
        "data": BudgetResponse(
            id=result.budget_id,
            department_id=result.department_id,
            fiscal_year=result.fiscal_year,
            allocated_amount_cents=(
                result.allocated_amount_cents
            ),
            spent_cents=result.spent_cents,
            remaining_cents=result.remaining_cents,
            utilization_pct=result.utilization_pct,
            currency=result.currency,
        ).model_dump(mode="json"),
    }


@router.get("/departments/{department_id}/budget")
def get_department_budget(
    department_id: str,
    fiscal_year: int = Query(None),
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    budget_repo: DepartmentBudgetRepository = Depends(
        get_budget_repo,
    ),
    budget_checker: BudgetChecker = Depends(
        get_budget_checker,
    ),
):
    handler = GetDepartmentBudgetQueryHandler(
        budget_repo=budget_repo,
        budget_checker=budget_checker,
    )
    result = handler.handle(
        GetDepartmentBudgetQuery(
            company_id=current_user.company_id,
            department_id=department_id,
            fiscal_year=fiscal_year,
        )
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No budget set for this department",
        )

    return {
        "data": BudgetResponse(
            id=result.budget_id,
            department_id=result.department_id,
            fiscal_year=result.fiscal_year,
            allocated_amount_cents=(
                result.allocated_amount_cents
            ),
            spent_cents=result.spent_cents,
            remaining_cents=result.remaining_cents,
            utilization_pct=result.utilization_pct,
            currency=result.currency,
        ).model_dump(mode="json"),
    }


@router.get("/budgets/summary")
def get_budget_summary(
    fiscal_year: int = Query(None),
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    budget_repo: DepartmentBudgetRepository = Depends(
        get_budget_repo,
    ),
    budget_checker: BudgetChecker = Depends(
        get_budget_checker,
    ),
):
    handler = GetBudgetSummaryQueryHandler(
        budget_repo=budget_repo,
        budget_checker=budget_checker,
    )
    result = handler.handle(
        GetBudgetSummaryQuery(
            company_id=current_user.company_id,
            fiscal_year=fiscal_year,
        )
    )

    return {
        "data": BudgetSummaryResponse(
            fiscal_year=result.fiscal_year,
            total_allocated_cents=(
                result.total_allocated_cents
            ),
            total_spent_cents=result.total_spent_cents,
            departments=[
                BudgetDepartmentItem(
                    department_id=d.department_id,
                    allocated_amount_cents=(
                        d.allocated_amount_cents
                    ),
                    spent_cents=d.spent_cents,
                    remaining_cents=d.remaining_cents,
                    utilization_pct=d.utilization_pct,
                    currency=d.currency,
                )
                for d in result.departments
            ],
        ).model_dump(mode="json"),
    }
