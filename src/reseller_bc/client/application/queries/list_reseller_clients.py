from dataclasses import dataclass

from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler
from src.reseller_bc.client.application.dtos import ResellerClientDto, ResellerClientListDto
from src.reseller_bc.client.domain.repository import ResellerClientRepositoryInterface


@dataclass
class ListResellerClientsQuery(Query):
    reseller_id: str
    offset: int = 0
    limit: int = 50


class ListResellerClientsQueryHandler(QueryHandler[ListResellerClientsQuery, ResellerClientListDto]):
    def __init__(
        self,
        client_repo: ResellerClientRepositoryInterface,
        company_repo: CompanyRepositoryInterface,
    ):
        self.client_repo = client_repo
        self.company_repo = company_repo

    def handle(self, query: ListResellerClientsQuery) -> ResellerClientListDto:
        clients = self.client_repo.find_by_reseller_id(
            query.reseller_id, offset=query.offset, limit=query.limit,
        )
        total = self.client_repo.count_by_reseller_id(query.reseller_id)

        # Batch fetch companies to avoid N+1
        items = []
        for client in clients:
            company = self.company_repo.find_by_id(client.company_id)
            if company:
                items.append(ResellerClientDto.from_entity_with_company(
                    client=client,
                    company_name=company.name,
                    plan=company.plan.value,
                    company_status=company.status.value,
                ))
            else:
                items.append(ResellerClientDto.from_entity_with_company(
                    client=client,
                    company_name="(deleted)",
                    plan="free",
                    company_status="deactivated",
                ))

        return ResellerClientListDto(items=items, total=total)
