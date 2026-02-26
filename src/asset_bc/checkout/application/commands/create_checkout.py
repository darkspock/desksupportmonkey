from dataclasses import dataclass
from typing import Optional

import ulid

from src.asset_bc.asset.domain.entities import AssetEvent
from src.asset_bc.asset.domain.enums import AssetStatus
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.asset_bc.checkout.application.ports import CheckoutUserLookup
from src.asset_bc.checkout.domain.entities import AssetCheckout
from src.asset_bc.checkout.domain.enums import AssetCondition
from src.asset_bc.checkout.domain.exceptions import (
    ActiveCheckoutExistsError,
    AssetAssignedToOtherError,
    InvalidCheckoutAssetStatusError,
)
from src.asset_bc.checkout.domain.repository import CheckoutRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


class AssetNotFoundError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserInactiveError(Exception):
    pass


@dataclass
class CreateCheckoutCommand(Command):
    checkout_id: str
    company_id: str
    asset_id: str
    user_id: str
    performed_by: str
    condition_out: str
    condition_out_notes: Optional[str] = None
    notes_out: Optional[str] = None


class CreateCheckoutCommandHandler(CommandHandler[CreateCheckoutCommand]):
    def __init__(
        self,
        asset_repo: AssetRepositoryInterface,
        checkout_repo: CheckoutRepositoryInterface,
        user_repo: CheckoutUserLookup,
    ):
        self.asset_repo = asset_repo
        self.checkout_repo = checkout_repo
        self.user_repo = user_repo

    def handle(self, command: CreateCheckoutCommand) -> None:
        asset = self.asset_repo.find_by_id(command.asset_id, command.company_id)
        if not asset:
            raise AssetNotFoundError(f"Asset '{command.asset_id}' not found")

        user = self.user_repo.find_by_id_and_company(command.user_id, command.company_id)
        if not user:
            raise UserNotFoundError(f"User '{command.user_id}' not found")
        if not user.is_active:
            raise UserInactiveError(f"User '{command.user_id}' is inactive")

        auto_assigned = False

        if asset.status == AssetStatus.IN_STOCK:
            # Auto-assign
            asset.assign(user_id=command.user_id, department_id=user.department_id)
            self.asset_repo.save(asset)
            self.asset_repo.save_event(
                AssetEvent.create(
                    asset_id=asset.id,
                    event_type="assigned",
                    data={
                        "user_id": command.user_id,
                        "assigned_by": command.performed_by,
                        "department_id": user.department_id,
                        "auto_assigned_by_checkout": True,
                    },
                    performed_by=command.performed_by,
                )
            )
            auto_assigned = True
        elif asset.status == AssetStatus.ASSIGNED:
            if asset.assigned_to != command.user_id:
                raise AssetAssignedToOtherError(command.asset_id, asset.assigned_to or "")
        else:
            raise InvalidCheckoutAssetStatusError(asset.status.value)

        # Ensure no active checkout
        existing_checkout = self.checkout_repo.find_active_by_asset(
            command.asset_id, command.company_id,
        )
        if existing_checkout:
            raise ActiveCheckoutExistsError(command.asset_id)

        checkout = AssetCheckout.create(
            company_id=command.company_id,
            asset_id=command.asset_id,
            user_id=command.user_id,
            checked_out_by=command.performed_by,
            condition_out=AssetCondition(command.condition_out),
            condition_out_notes=command.condition_out_notes,
            notes_out=command.notes_out,
            id=command.checkout_id,
            auto_assigned=auto_assigned,
        )
        self.checkout_repo.save(checkout)

        self.asset_repo.save_event(
            AssetEvent.create(
                asset_id=asset.id,
                event_type="checked_out",
                data={
                    "checkout_id": checkout.id,
                    "user_id": command.user_id,
                    "checked_out_by": command.performed_by,
                    "condition_out": command.condition_out,
                    "auto_assigned": auto_assigned,
                },
                performed_by=command.performed_by,
            )
        )
