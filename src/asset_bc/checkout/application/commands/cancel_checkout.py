from dataclasses import dataclass
from typing import Optional

from src.asset_bc.asset.domain.entities import AssetEvent
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.asset_bc.checkout.domain.exceptions import NoActiveCheckoutError
from src.asset_bc.checkout.domain.repository import CheckoutRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


class AssetNotFoundError(Exception):
    pass


@dataclass
class CancelCheckoutCommand(Command):
    asset_id: str
    company_id: str
    performed_by: str
    reason: Optional[str] = None


class CancelCheckoutCommandHandler(CommandHandler[CancelCheckoutCommand]):
    def __init__(
        self,
        asset_repo: AssetRepositoryInterface,
        checkout_repo: CheckoutRepositoryInterface,
    ):
        self.asset_repo = asset_repo
        self.checkout_repo = checkout_repo

    def handle(self, command: CancelCheckoutCommand) -> None:
        asset = self.asset_repo.find_by_id(command.asset_id, command.company_id)
        if not asset:
            raise AssetNotFoundError(f"Asset '{command.asset_id}' not found")

        checkout = self.checkout_repo.find_active_by_asset(
            command.asset_id, command.company_id,
        )
        if not checkout:
            raise NoActiveCheckoutError(command.asset_id)

        checkout.cancel(cancelled_by=command.performed_by, reason=command.reason)
        self.checkout_repo.save(checkout)

        # Restore asset to pre-checkout state
        if checkout.auto_assigned:
            asset.unassign()
            self.asset_repo.save(asset)

        self.asset_repo.save_event(
            AssetEvent.create(
                asset_id=asset.id,
                event_type="checkout_cancelled",
                data={
                    "checkout_id": checkout.id,
                    "cancelled_by": command.performed_by,
                    "reason": command.reason,
                    "auto_assigned_reverted": checkout.auto_assigned,
                },
                performed_by=command.performed_by,
            )
        )
