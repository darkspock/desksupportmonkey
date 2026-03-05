from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth_bc.company_lookup.domain.service import CompanyLookupInterface
from src.company_bc.company.infrastructure.models import (
    CompanyEmailDomainModel,
    CompanyModel,
)


class CompanyLookupService(CompanyLookupInterface):
    """Lookup company by email domain using CompanyEmailDomain table."""

    def __init__(self, session: Session):
        self.session = session

    def find_company_id_by_email_domain(self, email: str) -> Optional[str]:
        result = self.find_company_by_email_domain(email)
        if result is None:
            return None
        company_id, is_active = result
        return company_id if is_active else None

    def find_company_by_email_domain(self, email: str) -> Optional[tuple[str, bool]]:
        domain = self.extract_domain(email)
        result = self.session.execute(
            select(CompanyEmailDomainModel.company_id, CompanyModel.is_active)
            .join(CompanyModel, CompanyEmailDomainModel.company_id == CompanyModel.id)
            .where(CompanyEmailDomainModel.domain == domain)
        ).first()
        if result is None:
            return None
        return (result[0], result[1])

    def is_email_allowed_in_company(self, email: str, company_id: str) -> bool:
        domain = self.extract_domain(email)
        result = self.session.execute(
            select(CompanyEmailDomainModel.id)
            .where(CompanyEmailDomainModel.company_id == company_id)
            .where(CompanyEmailDomainModel.domain == domain)
        ).first()
        return result is not None

    def find_companies_by_email_domain(
        self, email: str
    ) -> list[tuple[str, str, bool]]:
        domain = self.extract_domain(email)
        results = self.session.execute(
            select(
                CompanyEmailDomainModel.company_id,
                CompanyModel.slug,
                CompanyModel.is_active,
            )
            .join(CompanyModel, CompanyEmailDomainModel.company_id == CompanyModel.id)
            .where(CompanyEmailDomainModel.domain == domain)
        ).all()
        return [(r[0], r[1], r[2]) for r in results]
