import logging

from fastapi import APIRouter, Depends, HTTPException, status

from adapters.http.api.registration.dependencies import (
    get_asset_repo,
    get_asset_type_repo,
    get_company_repo,
    get_magic_link_repo,
    get_stripe_client,
    get_user_repo,
)
from adapters.http.api.registration.schemas import RegisterCompanyRequest
from core.email import get_email_service
from core.stripe_client import StripeClient, StripeUnavailableError
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.asset_type_bc.definition.infrastructure.repository import (
    AssetTypeDefinitionRepository,
)
from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.company.application.commands.create_company import (
    CompanyNameExistsError,
    CreateCompanyCommand,
    CreateCompanyCommandHandler,
    DomainAlreadyTakenError,
    UserAlreadyExistsError,
)
from src.company_bc.company.infrastructure.repository import CompanyRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/register", tags=["registration"])


@router.post("", status_code=status.HTTP_201_CREATED)
def register_company(
    body: RegisterCompanyRequest,
    company_repo: CompanyRepository = Depends(get_company_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    magic_link_repo: MagicLinkRepository = Depends(get_magic_link_repo),
    stripe_client: StripeClient = Depends(get_stripe_client),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    asset_type_repo: AssetTypeDefinitionRepository = Depends(get_asset_type_repo),
):
    """Public endpoint for self-service company registration."""
    handler = CreateCompanyCommandHandler(
        company_repo=company_repo,
        user_repo=user_repo,
        magic_link_repo=magic_link_repo,
        email_service=get_email_service(),
        stripe_client=stripe_client,
        asset_repo=asset_repo,
        asset_type_repo=asset_type_repo,
    )
    cmd = CreateCompanyCommand(
        name=body.name, email_domains=body.email_domains, admin_email=body.admin_email,
    )
    try:
        handler.handle(cmd)
    except CompanyNameExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company with this name already exists")
    except DomainAlreadyTakenError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except UserAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")
    except StripeUnavailableError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="stripe_unavailable")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"data": {"message": "Company registered. Check your email for the magic link."}}
