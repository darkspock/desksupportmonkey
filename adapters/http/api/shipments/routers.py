import logging
from typing import Optional

import ulid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import (
    get_current_user,
    require_role,
)
from adapters.http.api.dependencies import get_event_bus
from adapters.http.api.shipments.dependencies import (
    get_delivery_asset_service,
    get_shipment_repo,
)
from adapters.http.api.shipments.schemas import (
    CancelShipmentRequest,
    CreateReturnRequest,
    CreateShipmentRequest,
    DeliverShipmentRequest,
    DispatchShipmentRequest,
    FailShipmentRequest,
    ModifyItemsRequest,
    ShipmentItemResponse,
    ShipmentResponse,
    UpdateShipmentRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.notification_bc.notification.application.services.event_bus import (
    EventBus,
)
from src.notification_bc.notification.application.services.shipment_event_factory import (
    ShipmentEventFactory,
)
from src.shipping_bc.shipment.application.commands.cancel_shipment import (
    CancelShipmentCommand,
    CancelShipmentCommandHandler,
)
from src.shipping_bc.shipment.application.commands.cancel_shipment import (
    ShipmentNotFoundError as CancelNotFoundError,
)
from src.shipping_bc.shipment.application.commands.create_return_shipment import (
    CreateReturnShipmentCommand,
    CreateReturnShipmentCommandHandler,
)
from src.shipping_bc.shipment.application.commands.create_return_shipment import (
    ShipmentNotFoundError as ReturnNotFoundError,
)
from src.shipping_bc.shipment.application.commands.create_shipment import (
    AssetConflictError,
    CreateShipmentCommand,
    CreateShipmentCommandHandler,
)
from src.shipping_bc.shipment.application.commands.deliver_shipment import (
    DeliverShipmentCommand,
    DeliverShipmentCommandHandler,
)
from src.shipping_bc.shipment.application.commands.deliver_shipment import (
    ShipmentNotFoundError as DeliverNotFoundError,
)
from src.shipping_bc.shipment.application.commands.dispatch_shipment import (
    DispatchShipmentCommand,
    DispatchShipmentCommandHandler,
)
from src.shipping_bc.shipment.application.commands.dispatch_shipment import (
    ShipmentNotFoundError as DispatchNotFoundError,
)
from src.shipping_bc.shipment.application.commands.fail_shipment import (
    FailShipmentCommand,
    FailShipmentCommandHandler,
)
from src.shipping_bc.shipment.application.commands.fail_shipment import (
    ShipmentNotFoundError as FailNotFoundError,
)
from src.shipping_bc.shipment.application.commands.mark_in_transit import (
    MarkInTransitCommand,
    MarkInTransitCommandHandler,
)
from src.shipping_bc.shipment.application.commands.mark_in_transit import (
    ShipmentNotFoundError as TransitNotFoundError,
)
from src.shipping_bc.shipment.application.commands.modify_shipment_items import (
    ModifyShipmentItemsCommand,
    ModifyShipmentItemsCommandHandler,
)
from src.shipping_bc.shipment.application.commands.modify_shipment_items import (
    ShipmentNotFoundError as ModifyNotFoundError,
)
from src.shipping_bc.shipment.application.commands.update_shipment import (
    UpdateShipmentCommand,
    UpdateShipmentCommandHandler,
)
from src.shipping_bc.shipment.application.commands.update_shipment import (
    ShipmentNotFoundError as UpdateNotFoundError,
)
from src.shipping_bc.shipment.application.queries.get_shipment import (
    GetShipmentQuery,
    GetShipmentQueryHandler,
)
from src.shipping_bc.shipment.application.queries.get_shipment import (
    ShipmentNotFoundError as GetNotFoundError,
)
from src.shipping_bc.shipment.application.queries.list_shipments import (
    ListShipmentsQuery,
    ListShipmentsQueryHandler,
)
from src.shipping_bc.shipment.application.queries.shipments_by_asset import (
    ShipmentsByAssetQuery,
    ShipmentsByAssetQueryHandler,
)
from src.shipping_bc.shipment.application.services.delivery_asset_service import (
    DeliveryAssetService,
)
from src.shipping_bc.shipment.domain.entities import Shipment
from src.shipping_bc.shipment.domain.enums import (
    InvalidShipmentStatusTransitionError,
)
from src.shipping_bc.shipment.infrastructure.repository import (
    ShipmentRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/shipments", tags=["shipments"],
)

tech_dep = require_role(UserRole.TECHNICIAN)


def _to_response(shipment: Shipment) -> dict:
    return ShipmentResponse(
        id=shipment.id,
        company_id=shipment.company_id,
        direction=shipment.direction.value,
        destination_type=shipment.destination_type.value,
        status=shipment.status.value,
        destination_address_id=shipment.destination_address_id,
        created_by=shipment.created_by,
        origin_address_id=shipment.origin_address_id,
        recipient_name=shipment.recipient_name,
        recipient_user_id=shipment.recipient_user_id,
        carrier=shipment.carrier,
        service_level=shipment.service_level,
        tracking_number=shipment.tracking_number,
        tracking_url=shipment.tracking_url,
        items_description=shipment.items_description,
        internal_notes=shipment.internal_notes,
        request_id=shipment.request_id,
        po_id=shipment.po_id,
        return_for_shipment_id=shipment.return_for_shipment_id,
        notes=shipment.notes,
        failure_reason=shipment.failure_reason,
        cancellation_reason=shipment.cancellation_reason,
        dispatched_at=shipment.dispatched_at,
        delivered_at=shipment.delivered_at,
        created_at=shipment.created_at,
        updated_at=shipment.updated_at,
        items=[
            ShipmentItemResponse(
                id=item.id,
                shipment_id=item.shipment_id,
                asset_id=item.asset_id,
                notes=item.notes,
            )
            for item in shipment.items
        ],
        item_count=len(shipment.items),
    ).model_dump(mode="json")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_shipment(
    body: CreateShipmentRequest,
    current_user: User = Depends(tech_dep),
    shipment_repo: ShipmentRepository = Depends(
        get_shipment_repo,
    ),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    shipment_id = ulid.new().str
    handler = CreateShipmentCommandHandler(
        shipment_repo=shipment_repo,
    )
    try:
        handler.handle(
            CreateShipmentCommand(
                shipment_id=shipment_id,
                company_id=current_user.company_id,
                direction=body.direction,
                destination_type=body.destination_type,
                destination_address_id=(
                    body.destination_address_id
                ),
                created_by=current_user.id,
                asset_ids=body.asset_ids,
                origin_address_id=body.origin_address_id,
                recipient_name=body.recipient_name,
                recipient_user_id=body.recipient_user_id,
                carrier=body.carrier,
                service_level=body.service_level,
                tracking_number=body.tracking_number,
                tracking_url=body.tracking_url,
                items_description=(
                    body.items_description
                ),
                internal_notes=body.internal_notes,
                request_id=body.request_id,
                po_id=body.po_id,
                notes=body.notes,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except AssetConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    shipment = shipment_repo.find_by_id(
        shipment_id, current_user.company_id,
    )
    event = ShipmentEventFactory.shipment_created(
        shipment, actor_id=current_user.id,
    )
    event_bus.publish(event, db)

    return {"data": _to_response(shipment)}


@router.get("")
def list_shipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    shipment_status: Optional[str] = Query(
        None, alias="status",
    ),
    direction: Optional[str] = Query(None),
    destination_type: Optional[str] = Query(None),
    request_id: Optional[str] = Query(None),
    po_id: Optional[str] = Query(None),
    current_user: User = Depends(tech_dep),
    shipment_repo: ShipmentRepository = Depends(
        get_shipment_repo,
    ),
):
    handler = ListShipmentsQueryHandler(
        shipment_repo=shipment_repo,
    )
    shipments, total = handler.handle(
        ListShipmentsQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            status=shipment_status,
            direction=direction,
            destination_type=destination_type,
            request_id=request_id,
            po_id=po_id,
        )
    )
    return {
        "data": [
            _to_response(s) for s in shipments
        ],
        "meta": PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
        ).model_dump(),
    }


@router.get("/by-asset/{asset_id}")
def shipments_by_asset(
    asset_id: str,
    current_user: User = Depends(tech_dep),
    shipment_repo: ShipmentRepository = Depends(
        get_shipment_repo,
    ),
):
    handler = ShipmentsByAssetQueryHandler(
        shipment_repo=shipment_repo,
    )
    shipments = handler.handle(
        ShipmentsByAssetQuery(
            asset_id=asset_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": [
            _to_response(s) for s in shipments
        ],
    }


@router.get("/{shipment_id}")
def get_shipment(
    shipment_id: str,
    current_user: User = Depends(get_current_user),
    shipment_repo: ShipmentRepository = Depends(
        get_shipment_repo,
    ),
):
    handler = GetShipmentQueryHandler(
        shipment_repo=shipment_repo,
    )
    try:
        shipment = handler.handle(
            GetShipmentQuery(
                shipment_id=shipment_id,
                company_id=current_user.company_id,
            )
        )
    except GetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )

    return {"data": _to_response(shipment)}


@router.patch("/{shipment_id}")
def update_shipment(
    shipment_id: str,
    body: UpdateShipmentRequest,
    current_user: User = Depends(tech_dep),
    shipment_repo: ShipmentRepository = Depends(
        get_shipment_repo,
    ),
):
    handler = UpdateShipmentCommandHandler(
        shipment_repo=shipment_repo,
    )
    try:
        handler.handle(
            UpdateShipmentCommand(
                shipment_id=shipment_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                carrier=body.carrier,
                service_level=body.service_level,
                tracking_number=body.tracking_number,
                tracking_url=body.tracking_url,
                items_description=(
                    body.items_description
                ),
                internal_notes=body.internal_notes,
                notes=body.notes,
            )
        )
    except UpdateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )

    shipment = shipment_repo.find_by_id(
        shipment_id, current_user.company_id,
    )
    return {"data": _to_response(shipment)}


@router.post("/{shipment_id}/dispatch")
def dispatch_shipment(
    shipment_id: str,
    body: DispatchShipmentRequest,
    current_user: User = Depends(tech_dep),
    shipment_repo: ShipmentRepository = Depends(
        get_shipment_repo,
    ),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = DispatchShipmentCommandHandler(
        shipment_repo=shipment_repo,
    )
    try:
        handler.handle(
            DispatchShipmentCommand(
                shipment_id=shipment_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                carrier=body.carrier,
                tracking_number=body.tracking_number,
                tracking_url=body.tracking_url,
            )
        )
    except DispatchNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except InvalidShipmentStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    shipment = shipment_repo.find_by_id(
        shipment_id, current_user.company_id,
    )
    event = ShipmentEventFactory.shipment_dispatched(
        shipment, actor_id=current_user.id,
    )
    event_bus.publish(event, db)

    return {"data": _to_response(shipment)}


@router.post("/{shipment_id}/in-transit")
def mark_in_transit(
    shipment_id: str,
    current_user: User = Depends(tech_dep),
    shipment_repo: ShipmentRepository = Depends(
        get_shipment_repo,
    ),
):
    handler = MarkInTransitCommandHandler(
        shipment_repo=shipment_repo,
    )
    try:
        handler.handle(
            MarkInTransitCommand(
                shipment_id=shipment_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except TransitNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    except InvalidShipmentStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    shipment = shipment_repo.find_by_id(
        shipment_id, current_user.company_id,
    )
    return {"data": _to_response(shipment)}


@router.post("/{shipment_id}/deliver")
def deliver_shipment(
    shipment_id: str,
    body: DeliverShipmentRequest,
    current_user: User = Depends(tech_dep),
    shipment_repo: ShipmentRepository = Depends(
        get_shipment_repo,
    ),
    delivery_service: DeliveryAssetService = Depends(
        get_delivery_asset_service,
    ),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = DeliverShipmentCommandHandler(
        shipment_repo=shipment_repo,
        delivery_asset_service=delivery_service,
    )
    try:
        handler.handle(
            DeliverShipmentCommand(
                shipment_id=shipment_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                notes=body.notes,
            )
        )
    except DeliverNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    except InvalidShipmentStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    shipment = shipment_repo.find_by_id(
        shipment_id, current_user.company_id,
    )
    event = ShipmentEventFactory.shipment_delivered(
        shipment, actor_id=current_user.id,
    )
    event_bus.publish(event, db)

    return {"data": _to_response(shipment)}


@router.post("/{shipment_id}/fail")
def fail_shipment(
    shipment_id: str,
    body: FailShipmentRequest,
    current_user: User = Depends(tech_dep),
    shipment_repo: ShipmentRepository = Depends(
        get_shipment_repo,
    ),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = FailShipmentCommandHandler(
        shipment_repo=shipment_repo,
    )
    try:
        handler.handle(
            FailShipmentCommand(
                shipment_id=shipment_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                reason=body.reason,
            )
        )
    except FailNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    except InvalidShipmentStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    shipment = shipment_repo.find_by_id(
        shipment_id, current_user.company_id,
    )
    event = ShipmentEventFactory.shipment_failed(
        shipment, actor_id=current_user.id,
    )
    event_bus.publish(event, db)

    return {"data": _to_response(shipment)}


@router.post("/{shipment_id}/cancel")
def cancel_shipment(
    shipment_id: str,
    body: CancelShipmentRequest,
    current_user: User = Depends(tech_dep),
    shipment_repo: ShipmentRepository = Depends(
        get_shipment_repo,
    ),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = CancelShipmentCommandHandler(
        shipment_repo=shipment_repo,
    )
    try:
        handler.handle(
            CancelShipmentCommand(
                shipment_id=shipment_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                reason=body.reason,
            )
        )
    except CancelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    except InvalidShipmentStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    shipment = shipment_repo.find_by_id(
        shipment_id, current_user.company_id,
    )
    event = ShipmentEventFactory.shipment_cancelled(
        shipment, actor_id=current_user.id,
    )
    event_bus.publish(event, db)

    return {"data": _to_response(shipment)}


@router.post(
    "/{shipment_id}/return",
    status_code=status.HTTP_201_CREATED,
)
def create_return_shipment(
    shipment_id: str,
    body: CreateReturnRequest,
    current_user: User = Depends(tech_dep),
    shipment_repo: ShipmentRepository = Depends(
        get_shipment_repo,
    ),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    return_id = ulid.new().str
    handler = CreateReturnShipmentCommandHandler(
        shipment_repo=shipment_repo,
    )
    try:
        handler.handle(
            CreateReturnShipmentCommand(
                return_shipment_id=return_id,
                original_shipment_id=shipment_id,
                company_id=current_user.company_id,
                created_by=current_user.id,
                destination_address_id=(
                    body.destination_address_id
                ),
                asset_ids=body.asset_ids,
                carrier=body.carrier,
                tracking_number=body.tracking_number,
                notes=body.notes,
            )
        )
    except ReturnNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original shipment not found",
        )
    except AssetConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    shipment = shipment_repo.find_by_id(
        return_id, current_user.company_id,
    )
    event = ShipmentEventFactory.shipment_created(
        shipment, actor_id=current_user.id,
    )
    event_bus.publish(event, db)

    return {"data": _to_response(shipment)}


@router.patch("/{shipment_id}/items")
def modify_items(
    shipment_id: str,
    body: ModifyItemsRequest,
    current_user: User = Depends(tech_dep),
    shipment_repo: ShipmentRepository = Depends(
        get_shipment_repo,
    ),
):
    handler = ModifyShipmentItemsCommandHandler(
        shipment_repo=shipment_repo,
    )
    try:
        handler.handle(
            ModifyShipmentItemsCommand(
                shipment_id=shipment_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                add_asset_ids=body.add_asset_ids,
                remove_item_ids=body.remove_item_ids,
            )
        )
    except ModifyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except AssetConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    shipment = shipment_repo.find_by_id(
        shipment_id, current_user.company_id,
    )
    return {"data": _to_response(shipment)}
