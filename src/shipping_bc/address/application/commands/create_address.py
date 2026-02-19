from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.shipping_bc.address.domain.entities import (
    ShippingAddress,
)
from src.shipping_bc.address.domain.repository import (
    ShippingAddressRepositoryInterface,
)


@dataclass
class CreateAddressCommand(Command):
    address_id: str
    company_id: str
    label: str
    street_line_1: str
    city: str
    state: str
    postal_code: str
    country: str = "US"
    street_line_2: Optional[str] = None
    recipient_name: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    is_office: bool = False


class CreateAddressCommandHandler(
    CommandHandler[CreateAddressCommand],
):
    def __init__(
        self,
        address_repo: ShippingAddressRepositoryInterface,
    ):
        self.address_repo = address_repo

    def handle(
        self, command: CreateAddressCommand,
    ) -> None:
        address = ShippingAddress.create(
            id=command.address_id,
            company_id=command.company_id,
            label=command.label,
            street_line_1=command.street_line_1,
            city=command.city,
            state=command.state,
            postal_code=command.postal_code,
            country=command.country,
            street_line_2=command.street_line_2,
            recipient_name=command.recipient_name,
            phone=command.phone,
            user_id=command.user_id,
            is_office=command.is_office,
        )
        self.address_repo.save(address)
