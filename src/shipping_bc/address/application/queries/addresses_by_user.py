from dataclasses import dataclass

from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)
from src.shipping_bc.address.domain.entities import (
    ShippingAddress,
)
from src.shipping_bc.address.domain.repository import (
    ShippingAddressRepositoryInterface,
)


@dataclass
class AddressesByUserQuery(Query):
    user_id: str
    company_id: str


class AddressesByUserQueryHandler(
    QueryHandler[
        AddressesByUserQuery, list[ShippingAddress],
    ],
):
    def __init__(
        self,
        address_repo: ShippingAddressRepositoryInterface,
    ):
        self.address_repo = address_repo

    def handle(
        self, query: AddressesByUserQuery,
    ) -> list[ShippingAddress]:
        return self.address_repo.find_by_user_id(
            query.user_id, query.company_id,
        )
