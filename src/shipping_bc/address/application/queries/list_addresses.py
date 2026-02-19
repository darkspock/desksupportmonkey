from dataclasses import dataclass
from typing import Optional

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
class ListAddressesQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    user_id: Optional[str] = None
    is_office: Optional[bool] = None
    is_active: Optional[bool] = True


class ListAddressesQueryHandler(
    QueryHandler[
        ListAddressesQuery,
        tuple[list[ShippingAddress], int],
    ],
):
    def __init__(
        self,
        address_repo: ShippingAddressRepositoryInterface,
    ):
        self.address_repo = address_repo

    def handle(
        self, query: ListAddressesQuery,
    ) -> tuple[list[ShippingAddress], int]:
        return self.address_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            user_id=query.user_id,
            is_office=query.is_office,
            is_active=query.is_active,
        )
