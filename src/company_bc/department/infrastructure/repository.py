from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.auth_bc.user.infrastructure.models import UserModel
from src.company_bc.department.domain.entities import Department
from src.company_bc.department.domain.repository import DepartmentRepositoryInterface
from src.company_bc.department.infrastructure.models import DepartmentModel


class DepartmentRepository(DepartmentRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, department: Department) -> Department:
        existing = self.session.execute(
            select(DepartmentModel).where(DepartmentModel.id == department.id)
        ).scalar_one_or_none()
        if existing:
            existing.name = department.name
            existing.is_active = department.is_active
        else:
            model = DepartmentModel(
                id=department.id,
                company_id=department.company_id,
                name=department.name,
                is_active=department.is_active,
            )
            self.session.add(model)
        self.session.flush()
        return department

    def find_by_id(self, department_id: str, company_id: str) -> Optional[Department]:
        model = self.session.execute(
            select(DepartmentModel).where(
                DepartmentModel.id == department_id,
                DepartmentModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_name(self, name: str, company_id: str) -> Optional[Department]:
        model = self.session.execute(
            select(DepartmentModel).where(
                func.lower(DepartmentModel.name) == name.lower().strip(),
                DepartmentModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all(
        self, company_id: str, page: int, page_size: int, include_inactive: bool = False
    ) -> tuple[list[Department], int]:
        stmt = select(DepartmentModel).where(
            DepartmentModel.company_id == company_id
        )
        if not include_inactive:
            stmt = stmt.where(DepartmentModel.is_active.is_(True))
        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()
        models = self.session.execute(
            stmt.order_by(DepartmentModel.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()
        return [self._to_entity(m) for m in models], total

    def count_users(self, department_id: str) -> int:
        return (
            self.session.execute(
                select(func.count()).select_from(UserModel)
                .where(UserModel.department_id == department_id)
            ).scalar()
        ) or 0

    @staticmethod
    def _to_entity(model: DepartmentModel) -> Department:
        return Department(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
