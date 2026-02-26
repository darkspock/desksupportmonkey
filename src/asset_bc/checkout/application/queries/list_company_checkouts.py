from dataclasses import dataclass
from typing import Optional

from src.asset_bc.checkout.application.dtos import CheckoutDto
from src.asset_bc.checkout.domain.repository import CheckoutRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class ListCompanyCheckoutsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    user_id: Optional[str] = None
    asset_id: Optional[str] = None


class ListCompanyCheckoutsQueryHandler(
    QueryHandler[ListCompanyCheckoutsQuery, tuple[list[CheckoutDto], int]],
):
    def __init__(self, checkout_repo: CheckoutRepositoryInterface):
        self.checkout_repo = checkout_repo

    def handle(self, query: ListCompanyCheckoutsQuery) -> tuple[list[CheckoutDto], int]:
        entities, total = self.checkout_repo.find_open_by_company(
            query.company_id,
            page=query.page,
            page_size=query.page_size,
            user_id=query.user_id,
            asset_id=query.asset_id,
        )
        return [CheckoutDto.from_entity(e) for e in entities], total
