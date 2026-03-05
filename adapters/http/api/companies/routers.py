import logging
from typing import Optional

import ulid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.companies.dependencies import (
    get_asset_repo,
    get_asset_type_repo,
    get_company_repo,
    get_magic_link_repo,
    get_maint_template_repo,
    get_stripe_client,
    get_user_repo,
    get_workflow_template_repo,
)
import dataclasses

from adapters.http.api.companies.schemas import (
    CompanyBillingResponse,
    CompanyBySlugResponse,
    CompanyDetailResponse,
    CompanyResponse,
    CreateCompanyRequest,
    GrantComplimentaryRequest,
    InvoiceResponse,
    OverridePlanRequest,
    UpdateCompanyRequest,
    UpdateCompanyStatusRequest,
    UpdateSlugRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from core.email import get_email_service
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.asset_type_bc.definition.infrastructure.repository import (
    AssetTypeDefinitionRepository,
)
from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository
from core.stripe_client import StripeClient, StripeUnavailableError
from src.maintenance_bc.maintenance_template.infrastructure.repository import (
    MaintenanceTemplateRepository,
)
from src.workflow_bc.template.infrastructure.repository import WorkflowTemplateRepository
from src.company_bc.company.application.commands.create_company import (
    CompanyNameExistsError,
    CreateCompanyCommand,
    CreateCompanyCommandHandler,
    DomainAlreadyTakenError,
    UserAlreadyExistsError,
)
from src.company_bc.company.application.commands.update_company import (
    CompanyNotFoundError as UpdateCompanyNotFoundError,
)
from src.company_bc.company.application.commands.update_company import (
    CompanyNameExistsError as UpdateNameExistsError,
)
from src.company_bc.company.application.commands.update_company import (
    DomainAlreadyTakenError as UpdateDomainTakenError,
)
from src.company_bc.company.application.commands.update_company import (
    UpdateCompanyCommand,
    UpdateCompanyCommandHandler,
)
from src.company_bc.company.application.queries.get_company import (
    CompanyNotFoundError,
    GetCompanyQuery,
    GetCompanyQueryHandler,
)
from src.company_bc.company.application.queries.list_companies import (
    CompanyListItemDto,
    ListCompaniesQuery,
    ListCompaniesQueryHandler,
)
from src.company_bc.company.application.commands.update_company_status import (
    CompanyNotFoundError as StatusCompanyNotFoundError,
    UpdateCompanyStatusCommand,
    UpdateCompanyStatusCommandHandler,
)
from src.company_bc.company.application.commands.billing.grant_complimentary_plan import (
    CompanyNotFoundError as GrantCompanyNotFoundError,
    GrantComplimentaryPlanCommand,
    GrantComplimentaryPlanCommandHandler,
)
from src.company_bc.company.application.commands.billing.override_company_plan import (
    CompanyNotFoundError as OverrideCompanyNotFoundError,
    OverrideCompanyPlanCommand,
    OverrideCompanyPlanCommandHandler,
)
from src.company_bc.company.application.commands.billing.revoke_complimentary_plan import (
    CompanyNotFoundError as RevokeCompanyNotFoundError,
    RevokeComplimentaryPlanCommand,
    RevokeComplimentaryPlanCommandHandler,
)
from src.company_bc.company.application.queries.billing.get_company_billing import (
    CompanyNotFoundError as BillingCompanyNotFoundError,
    GetCompanyBillingQuery,
    GetCompanyBillingQueryHandler,
)
from src.company_bc.company.application.queries.billing.get_company_invoices import (
    CompanyNotFoundError as InvoiceCompanyNotFoundError,
    GetCompanyInvoicesQuery,
    GetCompanyInvoicesQueryHandler,
)
from src.company_bc.company.application.commands.update_company_slug import (
    CompanyNotFoundError as SlugCompanyNotFoundError,
    UpdateCompanySlugCommand,
    UpdateCompanySlugCommandHandler,
)
from src.company_bc.company.application.queries.get_company_by_slug import (
    CompanyBySlugDto,
    CompanyNotFoundError as SlugResolveNotFoundError,
    GetCompanyBySlugQuery,
    GetCompanyBySlugQueryHandler,
)
from src.company_bc.company.domain.billing_enums import PlanTier
from src.company_bc.company.domain.entities import Company, InvalidStatusTransitionError, SlugAlreadyTakenError
from src.company_bc.company.infrastructure.repository import CompanyRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


def _to_response(company: Company) -> CompanyResponse:
    return CompanyResponse(
        id=company.id,
        name=company.name,
        slug=company.slug,
        status=company.status.value,
        email_domains=company.email_domains,
        is_active=company.is_active,
        auth_mode=company.auth_mode.value,
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


def _list_item_to_response(item: CompanyListItemDto) -> CompanyResponse:
    return CompanyResponse(
        id=item.id,
        name=item.name,
        status=item.status.value,
        email_domains=item.email_domains,
        is_active=item.is_active,
        created_at=item.created_at,
        updated_at=item.updated_at,
        plan=item.plan.value,
        billing_status=item.billing_status.value,
        user_count=item.user_count,
        asset_count=item.asset_count,
        trial_days_remaining=item.trial_days_remaining,
    )


def _get_company_response(company_repo: CompanyRepository, company_id: str) -> dict:
    query_handler = GetCompanyQueryHandler(company_repo=company_repo)
    detail = query_handler.handle(GetCompanyQuery(company_id=company_id))
    return {"data": _to_response(detail.company).model_dump(mode="json")}


def _handle_create_company_errors(handler: CreateCompanyCommandHandler, command: CreateCompanyCommand) -> None:
    try:
        handler.handle(command)
    except CompanyNameExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company with this name already exists",
        )
    except DomainAlreadyTakenError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )
    except StripeUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="stripe_unavailable",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_company(
    body: CreateCompanyRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    magic_link_repo: MagicLinkRepository = Depends(get_magic_link_repo),
    stripe_client: StripeClient = Depends(get_stripe_client),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    asset_type_repo: AssetTypeDefinitionRepository = Depends(get_asset_type_repo),
    workflow_template_repo: WorkflowTemplateRepository = Depends(get_workflow_template_repo),
    maint_template_repo: MaintenanceTemplateRepository = Depends(get_maint_template_repo),
):
    company_id = str(ulid.new())
    handler = CreateCompanyCommandHandler(
        company_repo=company_repo,
        user_repo=user_repo,
        magic_link_repo=magic_link_repo,
        email_service=get_email_service(),
        stripe_client=stripe_client,
        asset_repo=asset_repo,
        asset_type_repo=asset_type_repo,
        workflow_template_repo=workflow_template_repo,
        maint_template_repo=maint_template_repo,
    )
    command = CreateCompanyCommand(
        name=body.name,
        email_domains=body.email_domains,
        admin_email=body.admin_email,
        id=company_id,
    )
    _handle_create_company_errors(handler, command)
    return _get_company_response(company_repo, company_id)


@router.get("/by-slug/{slug}", response_model=dict)
def get_company_by_slug(
    slug: str,
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    """Public endpoint: resolve company slug to company info for login page."""
    from core.config import settings as app_settings

    handler = GetCompanyBySlugQueryHandler(
        company_repo=company_repo,
        oauth_settings=app_settings.oauth,
    )
    try:
        dto = handler.handle(GetCompanyBySlugQuery(slug=slug))
    except SlugResolveNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    return {
        "data": CompanyBySlugResponse(
            id=dto.id,
            name=dto.name,
            slug=dto.slug,
            auth_mode=dto.auth_mode,
            google_enabled=dto.google_enabled,
            microsoft_enabled=dto.microsoft_enabled,
        ).model_dump(mode="json")
    }


@router.patch("/{company_id}/slug")
def update_company_slug_super_admin(
    company_id: str,
    body: UpdateSlugRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    """Super admin updates any company's slug."""
    handler = UpdateCompanySlugCommandHandler(company_repo=company_repo)
    try:
        handler.handle(
            UpdateCompanySlugCommand(company_id=company_id, slug=body.slug)
        )
    except SlugCompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    except SlugAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Slug is already taken"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    return _get_company_response(company_repo, company_id)


@router.get("")
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    in_trial: Optional[bool] = Query(None),
    plan: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    handler = ListCompaniesQueryHandler(company_repo=company_repo)
    companies, total = handler.handle(
        ListCompaniesQuery(page=page, page_size=page_size, search=search, in_trial=in_trial, plan=plan)
    )
    return {
        "data": [_list_item_to_response(c).model_dump(mode="json") for c in companies],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.get("/{company_id}")
def get_company(
    company_id: str,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    handler = GetCompanyQueryHandler(company_repo=company_repo)
    try:
        detail = handler.handle(GetCompanyQuery(company_id=company_id))
    except CompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return {
        "data": CompanyDetailResponse(
            id=detail.company.id,
            name=detail.company.name,
            status=detail.company.status.value,
            email_domains=detail.company.email_domains,
            is_active=detail.company.is_active,
            created_at=detail.company.created_at,
            updated_at=detail.company.updated_at,
            user_count=detail.user_count,
            department_count=detail.department_count,
        ).model_dump(mode="json")
    }


@router.put("/{company_id}")
def update_company(
    company_id: str,
    body: UpdateCompanyRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    handler = UpdateCompanyCommandHandler(company_repo=company_repo)
    try:
        handler.handle(
            UpdateCompanyCommand(
                company_id=company_id,
                name=body.name,
                email_domains=body.email_domains,
            )
        )
    except UpdateCompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    except UpdateNameExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company with this name already exists",
        )
    except UpdateDomainTakenError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return _get_company_response(company_repo, company_id)


@router.patch("/{company_id}/status")
def update_company_status(
    company_id: str,
    body: UpdateCompanyStatusRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    handler = UpdateCompanyStatusCommandHandler(company_repo=company_repo)
    try:
        handler.handle(
            UpdateCompanyStatusCommand(
                company_id=company_id,
                new_status=body.status,
            )
        )
    except StatusCompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid status value. Must be: active, suspended, or deactivated",
        )
    return _get_company_response(company_repo, company_id)


def _billing_response(company_id: str, company_repo: CompanyRepository) -> dict:
    dto = GetCompanyBillingQueryHandler(company_repo=company_repo).handle(
        GetCompanyBillingQuery(company_id=company_id)
    )
    return {"data": CompanyBillingResponse(
        company_id=dto.company_id,
        company_name=dto.company_name,
        plan=dto.plan.value,
        billing_status=dto.billing_status.value,
        complimentary=dto.complimentary,
        stripe_customer_id=dto.stripe_customer_id,
        stripe_subscription_id=dto.stripe_subscription_id,
        current_period_end=dto.current_period_end,
        pending_downgrade_plan=dto.pending_downgrade_plan.value if dto.pending_downgrade_plan else None,
        grace_period_started_at=dto.grace_period_started_at,
        trial_days_remaining=dto.trial_days_remaining,
        trial_ends_at=dto.trial_ends_at,
    ).model_dump(mode="json")}


@router.get("/{company_id}/billing")
def get_company_billing(
    company_id: str,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    try:
        return _billing_response(company_id, company_repo)
    except BillingCompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")


@router.get("/{company_id}/invoices")
def get_company_invoices(
    company_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
    stripe_client: StripeClient = Depends(get_stripe_client),
):
    handler = GetCompanyInvoicesQueryHandler(
        company_repo=company_repo,
        stripe_client=stripe_client,
    )
    try:
        invoices = handler.handle(
            GetCompanyInvoicesQuery(company_id=company_id, limit=limit)
        )
    except InvoiceCompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    except StripeUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe unavailable",
        )
    return {
        "data": [
            InvoiceResponse(**dataclasses.asdict(inv)).model_dump(mode="json")
            for inv in invoices
        ]
    }


@router.patch("/{company_id}/billing/plan")
def override_company_billing_plan(
    company_id: str,
    body: OverridePlanRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    try:
        new_plan = PlanTier(body.new_plan)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid plan. Must be: free, premium, enterprise, or open_source",
        )
    handler = OverrideCompanyPlanCommandHandler(company_repo=company_repo)
    try:
        handler.handle(OverrideCompanyPlanCommand(company_id=company_id, new_plan=new_plan))
    except OverrideCompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return _billing_response(company_id, company_repo)


@router.post("/{company_id}/billing/complimentary", status_code=status.HTTP_200_OK)
def grant_complimentary_plan(
    company_id: str,
    body: GrantComplimentaryRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
    stripe_client: StripeClient = Depends(get_stripe_client),
):
    try:
        plan = PlanTier(body.plan)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid plan. Must be: free, premium, enterprise, or open_source",
        )
    handler = GrantComplimentaryPlanCommandHandler(
        company_repo=company_repo, stripe_client=stripe_client
    )
    try:
        handler.handle(GrantComplimentaryPlanCommand(company_id=company_id, plan=plan))
    except GrantCompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    except StripeUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="stripe_unavailable"
        )
    return _billing_response(company_id, company_repo)


@router.delete("/{company_id}/billing/complimentary", status_code=status.HTTP_200_OK)
def revoke_complimentary_plan(
    company_id: str,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    handler = RevokeComplimentaryPlanCommandHandler(company_repo=company_repo)
    try:
        handler.handle(RevokeComplimentaryPlanCommand(company_id=company_id))
    except RevokeCompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    return _billing_response(company_id, company_repo)
