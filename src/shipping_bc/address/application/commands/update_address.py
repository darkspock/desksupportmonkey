from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.shipping_bc.address.domain.repository import (
    ShippingAddressRepositoryInterface,
)


class AddressNotFoundError(Exception):
    pass


@dataclass
class UpdateAddressCommand(Command):
    address_id: str
    company_id: str
    label: Optional[str] = None
    street_line_1: Optional[str] = None
    street_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    recipient_name: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    is_office: Optional[bool] = None


class UpdateAddressCommandHandler(
    CommandHandler[UpdateAddressCommand],
):
    def __init__(
        self,
        address_repo: ShippingAddressRepositoryInterface,
    ):
        self.address_repo = address_repo

    def handle(
        self, command: UpdateAddressCommand,
    ) -> None:
        address = self.address_repo.find_by_id(
            command.address_id, command.company_id,
        )
        if not address:
            raise AddressNotFoundError(
                "Address not found",
            )

        address.update(
            label=command.label,
            street_line_1=command.street_line_1,
            street_line_2=command.street_line_2,
            city=command.city,
            state=command.state,
            postal_code=command.postal_code,
            country=command.country,
            recipient_name=command.recipient_name,
            phone=command.phone,
            user_id=command.user_id,
            is_office=command.is_office,
        )
        self.address_repo.save(address)
