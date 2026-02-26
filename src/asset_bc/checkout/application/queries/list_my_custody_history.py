from dataclasses import dataclass

from src.asset_bc.checkout.application.dtos import CheckoutDto
from src.asset_bc.checkout.domain.repository import CheckoutRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class ListMyCustodyHistoryQuery(Query):
    user_id: str
    company_id: str
    page: int = 1
    page_size: int = 20


class ListMyCustodyHistoryQueryHandler(
    QueryHandler[ListMyCustodyHistoryQuery, tuple[list[CheckoutDto], int]],
):
    def __init__(self, checkout_repo: CheckoutRepositoryInterface):
        self.checkout_repo = checkout_repo

    def handle(
        self, query: ListMyCustodyHistoryQuery
    ) -> tuple[list[CheckoutDto], int]:
        entities, total = self.checkout_repo.find_history_by_user(
            query.user_id,
            query.company_id,
            page=query.page,
            page_size=query.page_size,
        )
        return [CheckoutDto.from_entity(e) for e in entities], total
