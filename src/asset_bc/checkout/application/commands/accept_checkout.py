from dataclasses import dataclass

from src.asset_bc.asset.domain.entities import AssetEvent
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.asset_bc.checkout.domain.exceptions import NoActiveCheckoutError
from src.asset_bc.checkout.domain.repository import CheckoutRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class AcceptCheckoutCommand(Command):
    asset_id: str
    company_id: str
    user_id: str


class AcceptCheckoutCommandHandler(CommandHandler[AcceptCheckoutCommand]):
    def __init__(
        self,
        asset_repo: AssetRepositoryInterface,
        checkout_repo: CheckoutRepositoryInterface,
    ):
        self.asset_repo = asset_repo
        self.checkout_repo = checkout_repo

    def handle(self, command: AcceptCheckoutCommand) -> None:
        checkout = self.checkout_repo.find_active_by_asset(
            command.asset_id, command.company_id,
        )
        if not checkout:
            raise NoActiveCheckoutError(command.asset_id)

        checkout.accept(command.user_id)
        self.checkout_repo.save(checkout)

        self.asset_repo.save_event(
            AssetEvent.create(
                asset_id=checkout.asset_id,
                event_type="checkout_accepted",
                data={
                    "checkout_id": checkout.id,
                    "user_id": command.user_id,
                    "accepted_at": str(checkout.accepted_at),
                },
                performed_by=command.user_id,
            )
        )
