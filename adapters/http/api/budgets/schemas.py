from typing import Optional

from pydantic import BaseModel, Field


class BudgetSetRequest(BaseModel):
    fiscal_year: Optional[int] = None
    allocated_amount_cents: int = Field(ge=0)


class BudgetResponse(BaseModel):
    id: Optional[str] = None
    department_id: str
    fiscal_year: int
    allocated_amount_cents: int
    spent_cents: int
    remaining_cents: int
    utilization_pct: float
    currency: str


class BudgetDepartmentItem(BaseModel):
    department_id: str
    allocated_amount_cents: int
    spent_cents: int
    remaining_cents: int
    utilization_pct: float
    currency: str


class BudgetSummaryResponse(BaseModel):
    fiscal_year: int
    total_allocated_cents: int
    total_spent_cents: int
    departments: list[BudgetDepartmentItem]
