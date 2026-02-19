from dataclasses import dataclass

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
class DeactivateAddressCommand(Command):
    address_id: str
    company_id: str


class DeactivateAddressCommandHandler(
    CommandHandler[DeactivateAddressCommand],
):
    def __init__(
        self,
        address_repo: ShippingAddressRepositoryInterface,
    ):
        self.address_repo = address_repo

    def handle(
        self, command: DeactivateAddressCommand,
    ) -> None:
        address = self.address_repo.find_by_id(
            command.address_id, command.company_id,
        )
        if not address:
            raise AddressNotFoundError(
                "Address not found",
            )

        address.deactivate()
        self.address_repo.save(address)
