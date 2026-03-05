from dataclasses import dataclass

from core.config import OAuthSettings
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


class CompanyNotFoundError(Exception):
    pass


@dataclass
class CompanyBySlugDto:
    id: str
    name: str
    slug: str
    auth_mode: str
    google_enabled: bool
    microsoft_enabled: bool


@dataclass
class GetCompanyBySlugQuery(Query):
    slug: str


class GetCompanyBySlugQueryHandler(QueryHandler[GetCompanyBySlugQuery, CompanyBySlugDto]):
    def __init__(self, company_repo: CompanyRepositoryInterface, oauth_settings: OAuthSettings):
        self.company_repo = company_repo
        self.oauth_settings = oauth_settings

    def handle(self, query: GetCompanyBySlugQuery) -> CompanyBySlugDto:
        company = self.company_repo.find_by_slug(query.slug)
        if not company:
            raise CompanyNotFoundError(query.slug)
        if not company.is_active:
            raise CompanyNotFoundError(query.slug)
        return CompanyBySlugDto(
            id=company.id,
            name=company.name,
            slug=company.slug or query.slug,
            auth_mode=company.auth_mode.value,
            google_enabled=bool(self.oauth_settings.GOOGLE_CLIENT_ID),
            microsoft_enabled=bool(self.oauth_settings.MICROSOFT_CLIENT_ID),
        )
