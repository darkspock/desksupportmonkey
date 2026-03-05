import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.billing.dependencies import (
    get_billing_service,
    get_company_repo,
    get_stripe_client,
)
from core.database import get_db
from adapters.http.api.billing.schemas import (
    BillingOverviewResponse,
    CheckoutRequest,
    CheckoutResponse,
    PortalResponse,
)
from core.config import settings
from core.stripe_client import InvalidStripeSignatureError, StripeClient, StripeUnavailableError
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.company.application.queries.billing.get_billing_overview import (
    CompanyNotFoundError,
    GetBillingOverviewQuery,
    GetBillingOverviewQueryHandler,
)
from src.company_bc.company.application.services.stripe_billing_service import StripeBillingService
from src.company_bc.company.application.services.stripe_webhook_dispatcher import (
    StripeWebhookDispatcher,
)
from src.company_bc.company.domain.billing_enums import PlanTier
from src.company_bc.company.infrastructure.repository import CompanyRepository
from src.reseller_bc.client.infrastructure.repository import ResellerClientRepository
from src.reseller_bc.commission.infrastructure.repository import ResellerCommissionRepository
from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    company_repo: CompanyRepository = Depends(get_company_repo),
    stripe_client: StripeClient = Depends(get_stripe_client),
    db: Session = Depends(get_db),
):
    """Public endpoint — Stripe webhook receiver. Validates signature and dispatches events."""
    body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe_client.verify_webhook_signature(
            payload=body,
            sig_header=sig_header,
            webhook_secret=settings.stripe.STRIPE_WEBHOOK_SECRET,
        )
    except InvalidStripeSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_stripe_signature",
        )

    dispatcher = StripeWebhookDispatcher(
        company_repo=company_repo,
        client_repo=ResellerClientRepository(db),
        commission_repo=ResellerCommissionRepository(db),
        reseller_repo=ResellerRepository(db),
    )
    dispatcher.dispatch(event)

    return {"status": "ok"}


@router.get("/", response_model=BillingOverviewResponse)
def get_billing_overview(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    """Return billing overview for the authenticated admin's company."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="company_not_found")

    try:
        dto = GetBillingOverviewQueryHandler(company_repo).handle(
            GetBillingOverviewQuery(company_id=current_user.company_id)
        )
    except CompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="company_not_found")

    return BillingOverviewResponse(
        plan=dto.plan.value,
        billing_status=dto.billing_status.value,
        complimentary=dto.complimentary,
        user_count=dto.user_count,
        user_limit=dto.user_limit,
        asset_count=dto.asset_count,
        asset_limit=dto.asset_limit,
        grace_days_remaining=dto.grace_days_remaining,
        current_period_end=dto.current_period_end,
        pending_downgrade_plan=dto.pending_downgrade_plan.value if dto.pending_downgrade_plan else None,
        trial_days_remaining=dto.trial_days_remaining,
    )


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout_session(
    body: CheckoutRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
    billing_service: StripeBillingService = Depends(get_billing_service),
):
    """Create a Stripe Checkout session for plan upgrade."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="company_not_found")

    company = company_repo.find_by_id(current_user.company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="company_not_found")

    if not company.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="stripe_customer_not_provisioned",
        )

    try:
        target_plan = PlanTier(body.target_plan)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid_plan",
        )

    price_map = {
        PlanTier.STARTER: settings.stripe.STRIPE_PRICE_STARTER,
        PlanTier.PREMIUM: settings.stripe.STRIPE_PRICE_PREMIUM,
        PlanTier.ENTERPRISE: settings.stripe.STRIPE_PRICE_ENTERPRISE,
    }
    price_id = price_map.get(target_plan)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid_plan",
        )

    try:
        checkout_url = billing_service.create_checkout_session(
            stripe_customer_id=company.stripe_customer_id,
            target_plan=target_plan,
            price_id=price_id,
            success_url=f"{settings.FRONTEND_URL}/billing/processing",
            cancel_url=f"{settings.FRONTEND_URL}/billing",
        )
    except StripeUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="stripe_unavailable",
        )

    return CheckoutResponse(checkout_url=checkout_url)


@router.post("/portal", response_model=PortalResponse)
def create_portal_session(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
    billing_service: StripeBillingService = Depends(get_billing_service),
):
    """Create a Stripe Billing Portal session."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="company_not_found")

    company = company_repo.find_by_id(current_user.company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="company_not_found")

    if not company.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="stripe_customer_not_provisioned",
        )

    try:
        portal_url = billing_service.create_portal_session(
            stripe_customer_id=company.stripe_customer_id,
            return_url=f"{settings.FRONTEND_URL}/billing",
        )
    except StripeUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="stripe_unavailable",
        )

    return PortalResponse(portal_url=portal_url)
