from dataclasses import dataclass, field

from src.asset_bc.checkout.application.dtos import CheckoutDto
from src.asset_bc.checkout.domain.repository import CheckoutRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class MyEquipmentResult:
    open_checkouts: list[CheckoutDto] = field(default_factory=list)
    pending_acceptance: list[CheckoutDto] = field(default_factory=list)


@dataclass
class ListMyEquipmentQuery(Query):
    user_id: str
    company_id: str


class ListMyEquipmentQueryHandler(QueryHandler[ListMyEquipmentQuery, MyEquipmentResult]):
    def __init__(self, checkout_repo: CheckoutRepositoryInterface):
        self.checkout_repo = checkout_repo

    def handle(self, query: ListMyEquipmentQuery) -> MyEquipmentResult:
        open_entities = self.checkout_repo.find_open_by_user(
            query.user_id, query.company_id,
        )
        pending_entities = self.checkout_repo.find_pending_acceptance_by_user(
            query.user_id, query.company_id,
        )
        return MyEquipmentResult(
            open_checkouts=[CheckoutDto.from_entity(e) for e in open_entities],
            pending_acceptance=[CheckoutDto.from_entity(e) for e in pending_entities],
        )
