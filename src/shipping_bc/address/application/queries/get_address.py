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


class AddressNotFoundError(Exception):
    pass


@dataclass
class GetAddressQuery(Query):
    address_id: str
    company_id: str


class GetAddressQueryHandler(
    QueryHandler[GetAddressQuery, ShippingAddress],
):
    def __init__(
        self,
        address_repo: ShippingAddressRepositoryInterface,
    ):
        self.address_repo = address_repo

    def handle(
        self, query: GetAddressQuery,
    ) -> ShippingAddress:
        address = self.address_repo.find_by_id(
            query.address_id, query.company_id,
        )
        if not address:
            raise AddressNotFoundError(
                f"Address {query.address_id} not found",
            )
        return address
