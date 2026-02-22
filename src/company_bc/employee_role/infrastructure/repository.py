from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from src.company_bc.employee_role.domain.entities import EmployeeRole
from src.company_bc.employee_role.domain.repository import EmployeeRoleRepositoryInterface
from src.company_bc.employee_role.infrastructure.models import EmployeeRoleModel


class EmployeeRoleRepository(EmployeeRoleRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, role: EmployeeRole) -> EmployeeRole:
        existing = self.session.execute(
            select(EmployeeRoleModel).where(EmployeeRoleModel.id == role.id)
        ).scalar_one_or_none()
        if existing:
            existing.name = role.name
            existing.description = role.description
            existing.is_active = role.is_active
        else:
            model = EmployeeRoleModel(
                id=role.id,
                company_id=role.company_id,
                name=role.name,
                description=role.description,
                is_active=role.is_active,
            )
            self.session.add(model)
        self.session.flush()
        return role

    def find_by_id(self, role_id: str, company_id: str) -> Optional[EmployeeRole]:
        model = self.session.execute(
            select(EmployeeRoleModel).where(
                EmployeeRoleModel.id == role_id,
                EmployeeRoleModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_name(self, name: str, company_id: str) -> Optional[EmployeeRole]:
        model = self.session.execute(
            select(EmployeeRoleModel).where(
                func.lower(EmployeeRoleModel.name) == name.lower().strip(),
                EmployeeRoleModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all(
        self, company_id: str, page: int, page_size: int, include_inactive: bool = False
    ) -> tuple[list[EmployeeRole], int]:
        stmt = select(EmployeeRoleModel).where(
            EmployeeRoleModel.company_id == company_id
        )
        if not include_inactive:
            stmt = stmt.where(EmployeeRoleModel.is_active.is_(True))
        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()
        models = self.session.execute(
            stmt.order_by(EmployeeRoleModel.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()
        return [self._to_entity(m) for m in models], total or 0

    def delete(self, role_id: str) -> None:
        model = self.session.execute(
            select(EmployeeRoleModel).where(EmployeeRoleModel.id == role_id)
        ).scalar_one_or_none()
        if model:
            self.session.delete(model)
            self.session.flush()

    def count_users(self, role_id: str) -> int:
        return (
            self.session.execute(
                text("SELECT COUNT(*) FROM users WHERE employee_role_id = :role_id"),
                {"role_id": role_id},
            ).scalar()
        ) or 0

    def count_equipment_profiles(self, role_id: str) -> int:
        return (
            self.session.execute(
                text("SELECT COUNT(*) FROM equipment_profiles WHERE employee_role_id = :role_id"),
                {"role_id": role_id},
            ).scalar()
        ) or 0

    @staticmethod
    def _to_entity(model: EmployeeRoleModel) -> EmployeeRole:
        return EmployeeRole(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            description=model.description,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
