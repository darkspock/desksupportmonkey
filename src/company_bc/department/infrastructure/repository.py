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
            existing.manager_user_id = department.manager_user_id
            existing.priority_weight = department.priority_weight
        else:
            model = DepartmentModel(
                id=department.id,
                company_id=department.company_id,
                name=department.name,
                is_active=department.is_active,
                manager_user_id=department.manager_user_id,
                priority_weight=department.priority_weight,
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
        return [self._to_entity(m) for m in models], total or 0

    def find_manager_info(
        self, manager_user_id: str,
    ) -> Optional[tuple[str, Optional[str]]]:
        """Return (email, name) for a manager user ID."""
        model = self.session.execute(
            select(
                UserModel.email, UserModel.name,
            ).where(UserModel.id == manager_user_id)
        ).one_or_none()
        if model:
            return (model[0], model[1])
        return None

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
            manager_user_id=model.manager_user_id,
            priority_weight=model.priority_weight if model.priority_weight is not None else 0,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
