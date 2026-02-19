from typing import Optional

import ulid
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.enums import CompanyStatus
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.company_bc.company.infrastructure.models import (
    CompanyEmailDomainModel,
    CompanyModel,
)


class CompanyRepository(CompanyRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, company: Company) -> Company:
        existing = self.session.execute(
            select(CompanyModel).where(CompanyModel.id == company.id)
        ).scalar_one_or_none()
        if existing:
            existing.name = company.name
            existing.status = company.status.value
            existing.is_active = company.is_active
        else:
            model = CompanyModel(
                id=company.id,
                name=company.name,
                status=company.status.value,
                is_active=company.is_active,
            )
            self.session.add(model)
        self.session.flush()
        return company

    def find_by_id(self, company_id: str) -> Optional[Company]:
        model = self.session.execute(
            select(CompanyModel).where(CompanyModel.id == company_id)
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    def find_by_name(self, name: str) -> Optional[Company]:
        model = self.session.execute(
            select(CompanyModel).where(func.lower(CompanyModel.name) == name.lower().strip())
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    def find_all(
        self, page: int, page_size: int, search: Optional[str] = None
    ) -> tuple[list[Company], int]:
        stmt = select(CompanyModel)
        if search:
            stmt = stmt.where(CompanyModel.name.ilike(f"%{search}%"))
        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()
        models = self.session.execute(
            stmt.order_by(CompanyModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()
        return [self._to_entity(m) for m in models], total or 0

    def find_domain(self, domain: str) -> Optional[str]:
        result = self.session.execute(
            select(CompanyEmailDomainModel.company_id)
            .where(CompanyEmailDomainModel.domain == domain.lower().strip())
        ).scalar_one_or_none()
        return result if result else None

    def save_domains(self, company_id: str, domains: list[str]) -> None:
        self.session.execute(
            delete(CompanyEmailDomainModel)
            .where(CompanyEmailDomainModel.company_id == company_id)
        )
        for domain in domains:
            model = CompanyEmailDomainModel(
                id=str(ulid.new()),
                company_id=company_id,
                domain=domain.lower().strip(),
            )
            self.session.add(model)
        self.session.flush()

    def count_users(self, company_id: str) -> int:
        from src.auth_bc.user.infrastructure.models import UserModel

        return (
            self.session.execute(
                select(func.count()).select_from(UserModel)
                .where(UserModel.company_id == company_id)
            ).scalar()
        ) or 0

    def count_departments(self, company_id: str) -> int:
        try:
            from src.company_bc.department.infrastructure.models import DepartmentModel

            return (
                self.session.execute(
                    select(func.count()).select_from(DepartmentModel)
                    .where(
                        DepartmentModel.company_id == company_id,
                        DepartmentModel.is_active.is_(True),
                    )
                ).scalar()
            ) or 0
        except Exception:
            return 0

    def _to_entity(self, model: CompanyModel) -> Company:
        domains = self.session.execute(
            select(CompanyEmailDomainModel.domain)
            .where(CompanyEmailDomainModel.company_id == model.id)
        ).scalars().all()
        return Company(
            id=model.id,
            name=model.name,
            status=CompanyStatus(model.status),
            email_domains=list(domains),
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
