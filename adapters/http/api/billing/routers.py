import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from adapters.http.api.billing.dependencies import get_company_repo, get_stripe_client
from core.config import settings
from core.stripe_client import InvalidStripeSignatureError, StripeClient
from src.company_bc.company.application.services.stripe_webhook_dispatcher import (
    StripeWebhookDispatcher,
)
from src.company_bc.company.infrastructure.repository import CompanyRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    company_repo: CompanyRepository = Depends(get_company_repo),
    stripe_client: StripeClient = Depends(get_stripe_client),
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

    dispatcher = StripeWebhookDispatcher(company_repo=company_repo)
    dispatcher.dispatch(event)

    return {"status": "ok"}
