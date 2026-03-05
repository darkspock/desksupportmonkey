from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.auth_bc.company_user.domain.entities import CompanyUser
from src.auth_bc.company_user.domain.repository import CompanyUserRepositoryInterface
from src.auth_bc.company_user.infrastructure.models import CompanyUserModel
from src.auth_bc.user.domain.enums import UserRole


class CompanyUserRepository(CompanyUserRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, company_user: CompanyUser) -> CompanyUser:
        existing = self.session.execute(
            select(CompanyUserModel).where(CompanyUserModel.id == company_user.id)
        ).scalar_one_or_none()

        if existing:
            existing.role = company_user.role.value
            existing.department_id = company_user.department_id
            existing.employee_role_id = company_user.employee_role_id
            existing.is_active = company_user.is_active
        else:
            model = CompanyUserModel(
                id=company_user.id,
                user_id=company_user.user_id,
                company_id=company_user.company_id,
                role=company_user.role.value,
                department_id=company_user.department_id,
                employee_role_id=company_user.employee_role_id,
                is_active=company_user.is_active,
            )
            self.session.add(model)
        self.session.flush()
        return company_user

    def find_by_user_and_company(
        self, user_id: str, company_id: str
    ) -> Optional[CompanyUser]:
        model = self.session.execute(
            select(CompanyUserModel)
            .where(CompanyUserModel.user_id == user_id)
            .where(CompanyUserModel.company_id == company_id)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_user_id(self, user_id: str) -> list[CompanyUser]:
        models = (
            self.session.execute(
                select(CompanyUserModel).where(
                    CompanyUserModel.user_id == user_id
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def find_active_by_user_id(self, user_id: str) -> list[CompanyUser]:
        models = (
            self.session.execute(
                select(CompanyUserModel)
                .where(CompanyUserModel.user_id == user_id)
                .where(CompanyUserModel.is_active == True)  # noqa: E712
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def find_by_company_id(self, company_id: str) -> list[CompanyUser]:
        models = (
            self.session.execute(
                select(CompanyUserModel).where(
                    CompanyUserModel.company_id == company_id
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def count_admins_in_company(self, company_id: str) -> int:
        result = self.session.execute(
            select(func.count())
            .select_from(CompanyUserModel)
            .where(CompanyUserModel.company_id == company_id)
            .where(CompanyUserModel.role == UserRole.ADMIN.value)
            .where(CompanyUserModel.is_active == True)  # noqa: E712
        ).scalar()
        return result or 0

    def count_active_memberships(self, user_id: str) -> int:
        result = self.session.execute(
            select(func.count())
            .select_from(CompanyUserModel)
            .where(CompanyUserModel.user_id == user_id)
            .where(CompanyUserModel.is_active == True)  # noqa: E712
        ).scalar()
        return result or 0

    def _to_entity(self, model: CompanyUserModel) -> CompanyUser:
        return CompanyUser(
            id=model.id,
            user_id=model.user_id,
            company_id=model.company_id,
            role=UserRole(model.role),
            department_id=model.department_id,
            employee_role_id=model.employee_role_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
