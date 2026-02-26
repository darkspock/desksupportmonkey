from dataclasses import dataclass
from typing import Optional

from src.asset_bc.checkout.application.dtos import CheckoutDto
from src.asset_bc.checkout.domain.repository import CheckoutRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class GetCurrentCheckoutQuery(Query):
    asset_id: str
    company_id: str


class GetCurrentCheckoutQueryHandler(QueryHandler[GetCurrentCheckoutQuery, Optional[CheckoutDto]]):
    def __init__(self, checkout_repo: CheckoutRepositoryInterface):
        self.checkout_repo = checkout_repo

    def handle(self, query: GetCurrentCheckoutQuery) -> Optional[CheckoutDto]:
        entity = self.checkout_repo.find_active_by_asset(
            query.asset_id, query.company_id,
        )
        if not entity:
            return None
        return CheckoutDto.from_entity(entity)
