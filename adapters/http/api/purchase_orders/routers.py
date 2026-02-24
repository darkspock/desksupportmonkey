import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import (
    get_current_user,
)
from adapters.http.api.dependencies import get_event_bus
from adapters.http.api.purchase_orders.dependencies import (
    get_budget_checker,
    get_department_repo,
    get_po_repo,
    get_procurement_config_repo,
)
from adapters.http.api.purchase_orders.schemas import (
    CancelRequest,
    POCreateRequest,
    POItemResponse,
    POResponse,
    POUpdateRequest,
    ReceiveRequest,
    RejectRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.notification_bc.notification.application.services.event_bus import (  # noqa: E501
    EventBus,
)
from src.notification_bc.notification.domain.enums import (
    EventType,
)
from src.notification_bc.notification.domain.events import (
    DomainEvent,
)
from src.procurement_bc.budget.infrastructure.repository import (  # noqa: E501
    CompanyProcurementConfigRepository,
)
from src.procurement_bc.budget.application.services.budget_checker import (  # noqa: E501
    BudgetChecker,
)
from src.procurement_bc.purchase_order.application.commands.approve_po import (  # noqa: E501
    ApprovePurchaseOrderCommand,
    ApprovePurchaseOrderCommandHandler,
    BudgetExceededException,
    PONotFoundError as ApproveNotFoundError,
)
from src.procurement_bc.purchase_order.application.commands.cancel_po import (  # noqa: E501
    CancelPurchaseOrderCommand,
    CancelPurchaseOrderCommandHandler,
    PONotFoundError as CancelNotFoundError,
)
from src.procurement_bc.purchase_order.application.commands.close_po import (  # noqa: E501
    ClosePurchaseOrderCommand,
    ClosePurchaseOrderCommandHandler,
    InvalidCloseStatusError,
    PONotFoundError as CloseNotFoundError,
)
from src.procurement_bc.purchase_order.application.commands.create_po import (  # noqa: E501
    CreatePurchaseOrderCommand,
    CreatePurchaseOrderCommandHandler,
    POItemInput,
)
from src.procurement_bc.purchase_order.application.commands.mark_ordered import (  # noqa: E501
    MarkOrderedCommand,
    MarkOrderedCommandHandler,
    PONotFoundError as OrderedNotFoundError,
)
from src.procurement_bc.purchase_order.application.commands.receive_items import (  # noqa: E501
    InvalidReceiveQuantityError,
    InvalidReceiveStatusError,
    ItemNotFoundError,
    OverReceiveError,
    PONotFoundError as ReceiveNotFoundError,
    ReceiveItemInput,
    ReceiveItemsCommand,
    ReceiveItemsCommandHandler,
)
from src.procurement_bc.purchase_order.application.services.receipt_asset_service import (  # noqa: E501
    ReceiptAssetService,
)
from src.procurement_bc.purchase_order.application.commands.reject_po import (  # noqa: E501
    RejectPurchaseOrderCommand,
    RejectPurchaseOrderCommandHandler,
    PONotFoundError as RejectNotFoundError,
)
from src.procurement_bc.purchase_order.application.commands.submit_po import (  # noqa: E501
    SubmitPurchaseOrderCommand,
    SubmitPurchaseOrderCommandHandler,
    PONotFoundError as SubmitNotFoundError,
)
from src.procurement_bc.purchase_order.application.commands.update_po import (  # noqa: E501
    PONotDraftError,
    PONotFoundError as UpdateNotFoundError,
    UpdatePurchaseOrderCommand,
    UpdatePurchaseOrderCommandHandler,
)
from src.procurement_bc.purchase_order.application.queries.get_po import (  # noqa: E501
    GetPurchaseOrderQuery,
    GetPurchaseOrderQueryHandler,
    PONotFoundError as GetNotFoundError,
)
from src.procurement_bc.purchase_order.application.queries.list_pos import (  # noqa: E501
    ListPurchaseOrdersQuery,
    ListPurchaseOrdersQueryHandler,
)
from src.asset_bc.asset.infrastructure.repository import (
    AssetRepository,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
)
from src.procurement_bc.purchase_order.domain.enums import (
    InvalidPOStatusTransitionError,
    PurchaseOrderStatus,
)
from src.procurement_bc.purchase_order.infrastructure.repository import (  # noqa: E501
    PurchaseOrderRepository,
)
from src.company_bc.department.infrastructure.repository import (
    DepartmentRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/purchase-orders",
    tags=["purchase-orders"],
)


def _to_response(po: PurchaseOrder) -> POResponse:
    return POResponse(
        id=po.id,
        company_id=po.company_id,
        po_number=po.po_number,
        vendor_id=po.vendor_id,
        vendor_name=po.vendor_name,
        department_id=po.department_id,
        status=po.status.value,
        total_amount_cents=po.total_amount_cents,
        currency=po.currency,
        notes=po.notes,
        approved_by=po.approved_by,
        approved_at=po.approved_at,
        ordered_at=po.ordered_at,
        cancellation_reason=po.cancellation_reason,
        created_by=po.created_by,
        items=[
            POItemResponse(
                id=item.id,
                description=item.description,
                asset_type=item.asset_type,
                quantity=item.quantity,
                unit_cost_cents=item.unit_cost_cents,
                total_cost_cents=item.total_cost_cents,
                received_quantity=item.received_quantity,
                received_at=item.received_at,
                linked_asset_id=item.linked_asset_id,
                notes=item.notes,
            )
            for item in po.items
        ],
        request_ids=po.request_ids,
        created_at=po.created_at,
        updated_at=po.updated_at,
    )


def _require_technician(user: User) -> None:
    if not user.role.has_access(UserRole.TECHNICIAN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Technician access required",
        )


def _require_procurement_access(user: User) -> None:
    if not user.role.has_access(UserRole.PROCUREMENT_MANAGER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Procurement manager access required",
        )


def _po_event(
    event_type: str,
    po: PurchaseOrder,
    actor_id: str,
    **extra_payload,
) -> DomainEvent:
    payload = {
        "po_id": po.id,
        "po_number": po.po_number,
        "vendor_name": po.vendor_name,
        "total_amount_cents": po.total_amount_cents,
        "created_by": po.created_by,
        **extra_payload,
    }
    titles = {
        EventType.PO_SUBMITTED: f"PO {po.po_number} submitted",
        EventType.PO_APPROVED: f"PO {po.po_number} approved",
        EventType.PO_CANCELLED: f"PO {po.po_number} cancelled",
        EventType.PO_RECEIVED: f"PO {po.po_number} received",
    }
    bodies = {
        EventType.PO_SUBMITTED: (
            f"PO {po.po_number} — {po.vendor_name} — submitted for approval"
        ),
        EventType.PO_APPROVED: (
            f"PO {po.po_number} has been approved"
        ),
        EventType.PO_CANCELLED: (
            f"PO {po.po_number} has been cancelled"
        ),
        EventType.PO_RECEIVED: (
            f"PO {po.po_number} — all items received from {po.vendor_name}"
        ),
    }
    return DomainEvent(
        event_type=event_type,
        company_id=po.company_id,
        actor_id=actor_id,
        payload=payload,
        title=titles.get(event_type, "PO update"),
        body=bodies.get(event_type, "Purchase order updated"),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    body: POCreateRequest,
    current_user: User = Depends(get_current_user),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
    config_repo: CompanyProcurementConfigRepository = Depends(  # noqa: E501
        get_procurement_config_repo,
    ),
):
    _require_technician(current_user)

    handler = CreatePurchaseOrderCommandHandler(
        po_repo=po_repo,
        config_repo=config_repo,
    )
    try:
        handler.handle(
            CreatePurchaseOrderCommand(
                company_id=current_user.company_id,
                vendor_name=body.vendor_name,
                department_id=body.department_id,
                vendor_id=body.vendor_id,
                items=[
                    POItemInput(
                        description=i.description,
                        asset_type=i.asset_type,
                        quantity=i.quantity,
                        unit_cost_cents=i.unit_cost_cents,
                        notes=i.notes,
                    )
                    for i in body.items
                ],
                request_ids=body.request_ids,
                notes=body.notes,
                performed_by=current_user.id,
            )
        )
        po_id = handler.last_created_id
    except ValueError as e:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(e),
        )

    po = GetPurchaseOrderQueryHandler(
        po_repo=po_repo,
    ).handle(
        GetPurchaseOrderQuery(
            purchase_order_id=po_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(po).model_dump(mode="json"),
    }


@router.get("")
def list_purchase_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    po_status: str = Query(None, alias="status"),
    vendor_id: str = Query(None),
    department_id: str = Query(None),
    request_id: str = Query(None),
    current_user: User = Depends(get_current_user),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
):
    _require_technician(current_user)

    if request_id:
        pos = po_repo.find_by_request_id(
            request_id, current_user.company_id,
        )
        return {
            "data": [
                _to_response(po).model_dump(mode="json")
                for po in pos
            ],
            "meta": PaginationMeta(
                page=1,
                page_size=len(pos),
                total=len(pos),
            ).model_dump(),
        }

    handler = ListPurchaseOrdersQueryHandler(
        po_repo=po_repo,
    )
    pos, total = handler.handle(
        ListPurchaseOrdersQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            status=po_status,
            vendor_id=vendor_id,
            department_id=department_id,
        )
    )
    return {
        "data": [
            _to_response(po).model_dump(mode="json")
            for po in pos
        ],
        "meta": PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
        ).model_dump(),
    }


@router.get("/{purchase_order_id}")
def get_purchase_order(
    purchase_order_id: str,
    current_user: User = Depends(get_current_user),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
):
    _require_technician(current_user)

    try:
        po = GetPurchaseOrderQueryHandler(
            po_repo=po_repo,
        ).handle(
            GetPurchaseOrderQuery(
                purchase_order_id=purchase_order_id,
                company_id=current_user.company_id,
            )
        )
    except GetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )
    return {
        "data": _to_response(po).model_dump(mode="json"),
    }


@router.put("/{purchase_order_id}")
def update_purchase_order(
    purchase_order_id: str,
    body: POUpdateRequest,
    current_user: User = Depends(get_current_user),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
):
    _require_technician(current_user)

    handler = UpdatePurchaseOrderCommandHandler(
        po_repo=po_repo,
    )
    try:
        handler.handle(
            UpdatePurchaseOrderCommand(
                purchase_order_id=purchase_order_id,
                company_id=current_user.company_id,
                vendor_name=body.vendor_name,
                department_id=body.department_id,
                vendor_id=body.vendor_id,
                items=[
                    POItemInput(
                        description=i.description,
                        asset_type=i.asset_type,
                        quantity=i.quantity,
                        unit_cost_cents=i.unit_cost_cents,
                        notes=i.notes,
                    )
                    for i in body.items
                ],
                request_ids=body.request_ids,
                notes=body.notes,
                performed_by=current_user.id,
            )
        )
    except UpdateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )
    except PONotDraftError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only DRAFT purchase orders can be edited",
        )

    po = GetPurchaseOrderQueryHandler(
        po_repo=po_repo,
    ).handle(
        GetPurchaseOrderQuery(
            purchase_order_id=purchase_order_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(po).model_dump(mode="json"),
    }


@router.post("/{purchase_order_id}/submit")
def submit_purchase_order(
    purchase_order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
    config_repo: CompanyProcurementConfigRepository = Depends(  # noqa: E501
        get_procurement_config_repo,
    ),
    event_bus: EventBus = Depends(get_event_bus),
):
    _require_technician(current_user)

    handler = SubmitPurchaseOrderCommandHandler(
        po_repo=po_repo,
        config_repo=config_repo,
    )
    try:
        handler.handle(
            SubmitPurchaseOrderCommand(
                purchase_order_id=purchase_order_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
        result = handler.last_result
    except SubmitNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )
    except InvalidPOStatusTransitionError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Purchase order cannot be submitted",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(e),
        )

    po = GetPurchaseOrderQueryHandler(
        po_repo=po_repo,
    ).handle(
        GetPurchaseOrderQuery(
            purchase_order_id=purchase_order_id,
            company_id=current_user.company_id,
        )
    )

    if result.auto_approved:
        event = _po_event(
            EventType.PO_APPROVED,
            po,
            current_user.id,
        )
    else:
        event = _po_event(
            EventType.PO_SUBMITTED,
            po,
            current_user.id,
        )
    event_bus.publish(event, db)

    return {
        "data": _to_response(po).model_dump(mode="json"),
    }


@router.post("/{purchase_order_id}/approve")
def approve_purchase_order(
    purchase_order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
    dept_repo: DepartmentRepository = Depends(
        get_department_repo,
    ),
    budget_checker: BudgetChecker = Depends(
        get_budget_checker,
    ),
    event_bus: EventBus = Depends(get_event_bus),
):
    _require_procurement_access(current_user)

    handler = ApprovePurchaseOrderCommandHandler(
        po_repo=po_repo,
        budget_checker=budget_checker,
        department_repo=dept_repo,
    )
    try:
        handler.handle(
            ApprovePurchaseOrderCommand(
                purchase_order_id=purchase_order_id,
                company_id=current_user.company_id,
                approved_by=current_user.id,
            )
        )
        result = handler.last_result
    except ApproveNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )
    except InvalidPOStatusTransitionError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Purchase order cannot be approved",
        )
    except BudgetExceededException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    po = GetPurchaseOrderQueryHandler(
        po_repo=po_repo,
    ).handle(
        GetPurchaseOrderQuery(
            purchase_order_id=purchase_order_id,
            company_id=current_user.company_id,
        )
    )

    event = _po_event(
        EventType.PO_APPROVED, po, current_user.id,
    )
    event_bus.publish(event, db)

    if result.threshold_crossed:
        threshold_event = DomainEvent(
            event_type=EventType.BUDGET_THRESHOLD_REACHED,
            company_id=current_user.company_id,
            actor_id=current_user.id,
            payload={
                "department_id": result.department_id,
                "spent_cents": result.spent_cents,
                "allocated_cents": result.allocated_cents,
            },
            title="Budget threshold reached",
            body=(
                f"Department budget has reached "
                f"{result.spent_cents * 100 // result.allocated_cents}% "
                f"utilization"
            ),
        )
        event_bus.publish(threshold_event, db)

    response_data = _to_response(po).model_dump(
        mode="json",
    )
    if result.budget_warning:
        response_data["budget_warning"] = (
            result.budget_warning
        )

    return {"data": response_data}


@router.post("/{purchase_order_id}/reject")
def reject_purchase_order(
    purchase_order_id: str,
    body: RejectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
    event_bus: EventBus = Depends(get_event_bus),
):
    _require_procurement_access(current_user)

    handler = RejectPurchaseOrderCommandHandler(
        po_repo=po_repo,
    )
    try:
        handler.handle(
            RejectPurchaseOrderCommand(
                purchase_order_id=purchase_order_id,
                company_id=current_user.company_id,
                reason=body.reason,
                performed_by=current_user.id,
            )
        )
    except RejectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )
    except InvalidPOStatusTransitionError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Purchase order cannot be rejected",
        )

    po = GetPurchaseOrderQueryHandler(
        po_repo=po_repo,
    ).handle(
        GetPurchaseOrderQuery(
            purchase_order_id=purchase_order_id,
            company_id=current_user.company_id,
        )
    )

    event = _po_event(
        EventType.PO_CANCELLED,
        po,
        current_user.id,
        reason=body.reason,
    )
    event_bus.publish(event, db)

    return {
        "data": _to_response(po).model_dump(mode="json"),
    }


@router.post("/{purchase_order_id}/mark-ordered")
def mark_ordered(
    purchase_order_id: str,
    current_user: User = Depends(get_current_user),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
):
    _require_technician(current_user)

    handler = MarkOrderedCommandHandler(
        po_repo=po_repo,
    )
    try:
        handler.handle(
            MarkOrderedCommand(
                purchase_order_id=purchase_order_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except OrderedNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )
    except InvalidPOStatusTransitionError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Purchase order cannot be marked as ordered",
        )

    po = GetPurchaseOrderQueryHandler(
        po_repo=po_repo,
    ).handle(
        GetPurchaseOrderQuery(
            purchase_order_id=purchase_order_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(po).model_dump(mode="json"),
    }


@router.post("/{purchase_order_id}/receive")
def receive_items(
    purchase_order_id: str,
    body: ReceiveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
    event_bus: EventBus = Depends(get_event_bus),
):
    _require_technician(current_user)

    asset_repo = AssetRepository(db)
    receipt_service = ReceiptAssetService(
        asset_repo=asset_repo,
    )

    handler = ReceiveItemsCommandHandler(
        po_repo=po_repo,
        receipt_asset_service=receipt_service,
    )
    try:
        handler.handle(
            ReceiveItemsCommand(
                purchase_order_id=purchase_order_id,
                company_id=current_user.company_id,
                items=[
                    ReceiveItemInput(
                        item_id=i.item_id,
                        received_quantity=i.received_quantity,
                        create_asset=i.create_asset,
                        link_asset_id=i.link_asset_id,
                        location_id=i.location_id,
                    )
                    for i in body.items
                ],
                performed_by=current_user.id,
            )
        )
    except ReceiveNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )
    except InvalidReceiveStatusError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Purchase order cannot receive items",
        )
    except (OverReceiveError, InvalidReceiveQuantityError) as e:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(e),
        )
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    po = GetPurchaseOrderQueryHandler(
        po_repo=po_repo,
    ).handle(
        GetPurchaseOrderQuery(
            purchase_order_id=purchase_order_id,
            company_id=current_user.company_id,
        )
    )

    if po.status.value == "RECEIVED":
        event = _po_event(
            EventType.PO_RECEIVED,
            po,
            current_user.id,
        )
        event_bus.publish(event, db)

    return {
        "data": _to_response(po).model_dump(mode="json"),
    }


@router.post("/{purchase_order_id}/close")
def close_purchase_order(
    purchase_order_id: str,
    current_user: User = Depends(get_current_user),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
):
    _require_technician(current_user)

    handler = ClosePurchaseOrderCommandHandler(
        po_repo=po_repo,
    )
    try:
        handler.handle(
            ClosePurchaseOrderCommand(
                purchase_order_id=purchase_order_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except CloseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )
    except InvalidCloseStatusError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Purchase order cannot be closed",
        )
    except InvalidPOStatusTransitionError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Purchase order cannot be closed",
        )

    po = GetPurchaseOrderQueryHandler(
        po_repo=po_repo,
    ).handle(
        GetPurchaseOrderQuery(
            purchase_order_id=purchase_order_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(po).model_dump(mode="json"),
    }


@router.post("/{purchase_order_id}/cancel")
def cancel_purchase_order(
    purchase_order_id: str,
    body: CancelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
    event_bus: EventBus = Depends(get_event_bus),
):
    _require_technician(current_user)

    po_before = GetPurchaseOrderQueryHandler(
        po_repo=po_repo,
    ).handle(
        GetPurchaseOrderQuery(
            purchase_order_id=purchase_order_id,
            company_id=current_user.company_id,
        )
    )
    was_past_draft = po_before.status.value != "DRAFT"

    handler = CancelPurchaseOrderCommandHandler(
        po_repo=po_repo,
    )
    try:
        handler.handle(
            CancelPurchaseOrderCommand(
                purchase_order_id=purchase_order_id,
                company_id=current_user.company_id,
                reason=body.reason,
                performed_by=current_user.id,
            )
        )
    except CancelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )
    except InvalidPOStatusTransitionError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Purchase order cannot be cancelled",
        )

    po = GetPurchaseOrderQueryHandler(
        po_repo=po_repo,
    ).handle(
        GetPurchaseOrderQuery(
            purchase_order_id=purchase_order_id,
            company_id=current_user.company_id,
        )
    )

    if was_past_draft:
        event = _po_event(
            EventType.PO_CANCELLED,
            po,
            current_user.id,
            reason=body.reason,
        )
        event_bus.publish(event, db)

    return {
        "data": _to_response(po).model_dump(mode="json"),
    }


PDF_ELIGIBLE_STATUSES = {
    PurchaseOrderStatus.APPROVED,
    PurchaseOrderStatus.ORDERED,
    PurchaseOrderStatus.PARTIALLY_RECEIVED,
    PurchaseOrderStatus.RECEIVED,
    PurchaseOrderStatus.CLOSED,
}


@router.post("/{purchase_order_id}/pdf")
def generate_purchase_order_pdf(
    purchase_order_id: str,
    current_user: User = Depends(get_current_user),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
):
    _require_technician(current_user)

    try:
        po = GetPurchaseOrderQueryHandler(
            po_repo=po_repo,
        ).handle(
            GetPurchaseOrderQuery(
                purchase_order_id=purchase_order_id,
                company_id=current_user.company_id,
            )
        )
    except GetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    if po.status not in PDF_ELIGIBLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "PDF can only be generated for approved or later POs"
            ),
        )

    from core.tasks.reports import generate_po_pdf  # noqa: E501

    generate_po_pdf.delay(
        po.id, current_user.company_id,
    )

    return {"data": {"status": "generating"}}


@router.get("/{purchase_order_id}/pdf")
def get_purchase_order_pdf(
    purchase_order_id: str,
    current_user: User = Depends(get_current_user),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
):
    _require_technician(current_user)

    try:
        GetPurchaseOrderQueryHandler(
            po_repo=po_repo,
        ).handle(
            GetPurchaseOrderQuery(
                purchase_order_id=purchase_order_id,
                company_id=current_user.company_id,
            )
        )
    except GetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    from core.storage import S3StorageService

    storage_key = (
        f"po-pdfs/{current_user.company_id}/"
        f"{purchase_order_id}.pdf"
    )
    storage = S3StorageService()
    try:
        storage.client.head_object(
            Bucket=storage.bucket, Key=storage_key,
        )
        url = storage.get_signed_url(storage_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not yet generated",
        )

    return {"data": {"download_url": url}}
