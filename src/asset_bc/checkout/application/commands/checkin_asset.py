from dataclasses import dataclass
from typing import Optional

import ulid

from src.asset_bc.asset.domain.entities import AssetEvent
from src.asset_bc.asset.domain.enums import AssetStatus
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.asset_bc.checkout.application.ports import MaintenanceRecordCreator
from src.asset_bc.checkout.domain.enums import AssetCondition
from src.asset_bc.checkout.domain.exceptions import NoActiveCheckoutError
from src.asset_bc.checkout.domain.repository import CheckoutRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


class AssetNotFoundError(Exception):
    pass


@dataclass
class CheckinAssetCommand(Command):
    asset_id: str
    company_id: str
    performed_by: str
    condition_in: str
    condition_in_notes: Optional[str] = None
    notes_in: Optional[str] = None


class CheckinAssetCommandHandler(CommandHandler[CheckinAssetCommand]):
    def __init__(
        self,
        asset_repo: AssetRepositoryInterface,
        checkout_repo: CheckoutRepositoryInterface,
        maintenance_creator: MaintenanceRecordCreator,
    ):
        self.asset_repo = asset_repo
        self.checkout_repo = checkout_repo
        self.maintenance_creator = maintenance_creator

    def handle(self, command: CheckinAssetCommand) -> None:
        asset = self.asset_repo.find_by_id(command.asset_id, command.company_id)
        if not asset:
            raise AssetNotFoundError(f"Asset '{command.asset_id}' not found")

        checkout = self.checkout_repo.find_active_by_asset(
            command.asset_id, command.company_id,
        )
        if not checkout:
            raise NoActiveCheckoutError(command.asset_id)

        condition_in = AssetCondition(command.condition_in)
        checkout.checkin(
            checked_in_by=command.performed_by,
            condition_in=condition_in,
            condition_in_notes=command.condition_in_notes,
            notes_in=command.notes_in,
        )

        # Determine next asset status
        if condition_in == AssetCondition.UNUSABLE:
            asset.change_status(AssetStatus.DECOMMISSIONED)
        else:
            asset.change_status(AssetStatus.IN_REPAIR)

        # Unassign the asset
        asset.assigned_to = None
        asset.department_id = None

        self.asset_repo.save(asset)

        # Create GDPR sanitization maintenance record via port
        maintenance_id = str(ulid.new())
        title = f"GDPR Sanitization — {asset.brand} {asset.model}"
        self.maintenance_creator.create(
            record_id=maintenance_id,
            company_id=command.company_id,
            asset_id=command.asset_id,
            title=title,
            created_by=command.performed_by,
            priority="HIGH",
            description=f"Mandatory GDPR data sanitization after checkin. Condition: {condition_in.value}",
            source_type="checkout_gdpr",
        )

        checkout.maintenance_id = maintenance_id
        self.checkout_repo.save(checkout)

        self.asset_repo.save_event(
            AssetEvent.create(
                asset_id=asset.id,
                event_type="checked_in",
                data={
                    "checkout_id": checkout.id,
                    "checked_in_by": command.performed_by,
                    "condition_in": condition_in.value,
                    "maintenance_id": maintenance_id,
                    "new_status": asset.status.value,
                },
                performed_by=command.performed_by,
            )
        )
