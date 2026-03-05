import ulid
from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from sqlalchemy.orm import Session

from core.containers.reseller import ResellerContainer
from core.database import get_db
from adapters.http.api.reseller.dependencies import (
    get_current_reseller,
    get_password_login_service,
    get_reseller_command_bus,
    get_reseller_container,
    get_reseller_google_oauth_service,
    get_reseller_microsoft_oauth_service,
    get_reseller_query_bus,
    require_active_reseller,
)
from adapters.http.api.reseller.mappers import CommissionMapper, InvitationMapper, PayoutMapper, ResellerClientMapper, ResellerMapper
from adapters.http.api.reseller.schemas import (
    ChangePasswordRequest,
    CreateClientAccountRequest,
    CreateDemoAccountRequest,
    CreateInvitationRequest,
    ForgotPasswordRequest,
    OAuthLoginRequest,
    OAuthRegisterRequest,
    PasswordLoginRequest,
    ResellerRegisterRequest,
    ResetPasswordRequest,
    UpdateResellerProfileRequest,
)
from src.framework.application.command_bus import CommandBus
from src.framework.application.query_bus import QueryBus
from src.reseller_bc.reseller.application.commands.change_password import (
    ChangeResellerPasswordCommand,
)
from src.reseller_bc.reseller.application.commands.forgot_password import (
    ForgotResellerPasswordCommand,
)
from src.reseller_bc.reseller.application.commands.password_login import (
    ResellerPasswordLoginService,
)
from src.reseller_bc.reseller.application.commands.register_reseller import (
    RegisterResellerCommand,
)
from src.reseller_bc.reseller.application.commands.register_reseller_oauth import (
    RegisterResellerOAuthCommand,
)
from src.reseller_bc.reseller.application.commands.reset_password import (
    ResetResellerPasswordCommand,
)
from src.reseller_bc.reseller.application.commands.update_reseller_profile import (
    UpdateResellerProfileCommand,
)
from src.reseller_bc.reseller.application.queries.get_reseller_by_id import (
    GetResellerByIdQuery,
)
from src.reseller_bc.reseller.application.queries.get_reseller_dashboard import (
    GetResellerDashboardQuery,
)
from src.reseller_bc.reseller.application.services.reseller_google_oauth import (
    GoogleOAuthLoginRequest,
    ResellerGoogleNotConfiguredError,
    ResellerGoogleTokenInvalidError,
    ResellerGoogleEmailNotVerified,
)
from src.reseller_bc.reseller.application.services.reseller_microsoft_oauth import (
    MicrosoftOAuthLoginRequest,
    ResellerMicrosoftNotConfiguredError,
    ResellerMicrosoftTokenInvalidError,
    ResellerMicrosoftMissingEmail,
)
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerAlreadyExistsException,
    ResellerDeactivatedException,
    ResellerInvalidPasswordException,
    ResellerInvalidResetTokenException,
    ResellerNotFoundException,
    ResellerNotRegisteredException,
    ResellerOAuthProviderAlreadyLinkedError,
    ResellerPendingApprovalException,
)

router = APIRouter(prefix="/api/v1/reseller", tags=["reseller"])


@router.post("/auth/google")
def reseller_google_oauth_login(
    body: OAuthLoginRequest,
    service=Depends(get_reseller_google_oauth_service),
):
    try:
        access_token = service.handle(GoogleOAuthLoginRequest(id_token=body.id_token))
    except ResellerGoogleNotConfiguredError:
        raise HTTPException(status_code=501, detail="Google OAuth is not configured")
    except ResellerGoogleTokenInvalidError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ResellerGoogleEmailNotVerified as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ResellerNotRegisteredException as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ResellerPendingApprovalException:
        raise HTTPException(status_code=403, detail="Your account is pending approval")
    except ResellerDeactivatedException as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ResellerOAuthProviderAlreadyLinkedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"data": {"access_token": access_token}}


@router.post("/auth/microsoft")
def reseller_microsoft_oauth_login(
    body: OAuthLoginRequest,
    service=Depends(get_reseller_microsoft_oauth_service),
):
    try:
        access_token = service.handle(MicrosoftOAuthLoginRequest(id_token=body.id_token))
    except ResellerMicrosoftNotConfiguredError:
        raise HTTPException(status_code=501, detail="Microsoft OAuth is not configured")
    except ResellerMicrosoftTokenInvalidError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ResellerMicrosoftMissingEmail as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ResellerNotRegisteredException as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ResellerPendingApprovalException:
        raise HTTPException(status_code=403, detail="Your account is pending approval")
    except ResellerDeactivatedException as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ResellerOAuthProviderAlreadyLinkedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"data": {"access_token": access_token}}


@router.post("/auth/register", status_code=201)
def reseller_register(
    body: ResellerRegisterRequest,
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
):
    try:
        cmd_bus.dispatch(RegisterResellerCommand(
            name=body.name,
            email=body.email,
            company_name=body.company_name,
            password=body.password,
        ))
    except ResellerAlreadyExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ResellerInvalidPasswordException as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"message": "Registration submitted. Check your email for confirmation."}


@router.post("/auth/register/google", status_code=201)
def reseller_register_google(
    body: OAuthRegisterRequest,
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
):
    from core.config import settings
    from src.auth_bc.user.application.services.google_token_verifier import (
        GoogleEmailNotVerifiedError,
        GoogleTokenVerificationError,
        GoogleTokenVerifier,
    )

    if not settings.oauth.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth is not configured")

    verifier = GoogleTokenVerifier(settings.oauth.GOOGLE_CLIENT_ID)
    try:
        user_info = verifier.verify(body.id_token)
    except GoogleEmailNotVerifiedError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except GoogleTokenVerificationError as e:
        raise HTTPException(status_code=401, detail=str(e))

    try:
        cmd_bus.dispatch(RegisterResellerOAuthCommand(
            name=user_info.name or user_info.email.split("@")[0],
            email=user_info.email,
            company_name=body.company_name,
            provider_field="google_id",
            provider_id=user_info.sub,
        ))
    except ResellerAlreadyExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"message": "Registration submitted. Check your email for confirmation."}


@router.post("/auth/register/microsoft", status_code=201)
def reseller_register_microsoft(
    body: OAuthRegisterRequest,
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
):
    from core.config import settings
    from src.auth_bc.user.application.services.microsoft_token_verifier import (
        MicrosoftMissingEmailError,
        MicrosoftTokenVerificationError,
        MicrosoftTokenVerifier,
    )

    if not settings.oauth.MICROSOFT_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Microsoft OAuth is not configured")

    verifier = MicrosoftTokenVerifier(
        client_id=settings.oauth.MICROSOFT_CLIENT_ID,
        tenant_id=settings.oauth.MICROSOFT_TENANT_ID or "common",
    )
    try:
        user_info = verifier.verify(body.id_token)
    except MicrosoftMissingEmailError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except MicrosoftTokenVerificationError as e:
        raise HTTPException(status_code=401, detail=str(e))

    try:
        cmd_bus.dispatch(RegisterResellerOAuthCommand(
            name=user_info.name or user_info.email.split("@")[0],
            email=user_info.email,
            company_name=body.company_name,
            provider_field="microsoft_id",
            provider_id=user_info.oid,
        ))
    except ResellerAlreadyExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"message": "Registration submitted. Check your email for confirmation."}


@router.post("/auth/login")
def reseller_password_login(
    body: PasswordLoginRequest,
    service: ResellerPasswordLoginService = Depends(get_password_login_service),
):
    try:
        access_token = service.login(email=body.email, password=body.password)
    except ResellerNotRegisteredException:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    except ResellerInvalidPasswordException as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ResellerPendingApprovalException:
        raise HTTPException(status_code=403, detail="Your account is pending approval")
    except ResellerDeactivatedException:
        raise HTTPException(status_code=401, detail="Your account has been deactivated")
    return {"data": {"access_token": access_token}}


@router.post("/auth/forgot-password")
def reseller_forgot_password(
    body: ForgotPasswordRequest,
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
):
    cmd_bus.dispatch(ForgotResellerPasswordCommand(email=body.email))
    return {"message": "If an account exists with that email, you will receive a reset link."}


@router.post("/auth/reset-password")
def reseller_reset_password(
    body: ResetPasswordRequest,
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
):
    try:
        cmd_bus.dispatch(ResetResellerPasswordCommand(
            token=body.token, new_password=body.password,
        ))
    except ResellerInvalidResetTokenException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResellerInvalidPasswordException as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"message": "Password has been reset successfully."}


@router.post("/change-password")
def reseller_change_password(
    body: ChangePasswordRequest,
    current_reseller: Reseller = Depends(get_current_reseller),
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
):
    try:
        cmd_bus.dispatch(ChangeResellerPasswordCommand(
            reseller_id=current_reseller.id,
            current_password=body.current_password,
            new_password=body.new_password,
        ))
    except ResellerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ResellerInvalidPasswordException as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Password changed successfully."}


@router.get("/me")
def get_me(
    current_reseller: Reseller = Depends(get_current_reseller),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    try:
        dto = query_bus.query(GetResellerByIdQuery(reseller_id=current_reseller.id))
    except ResellerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    if dto is None:
        raise HTTPException(status_code=404, detail="Reseller not found")
    return {"data": ResellerMapper.dto_to_response(dto).model_dump()}


@router.put("/profile")
def update_profile(
    body: UpdateResellerProfileRequest,
    current_reseller: Reseller = Depends(require_active_reseller()),
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    try:
        cmd_bus.dispatch(UpdateResellerProfileCommand(
            reseller_id=current_reseller.id,
            company_name=body.company_name,
            tax_id=body.tax_id,
        ))
    except ResellerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Return updated reseller
    dto = query_bus.query(GetResellerByIdQuery(reseller_id=current_reseller.id))
    if dto is None:
        raise HTTPException(status_code=404, detail="Reseller not found")
    return {"data": ResellerMapper.dto_to_response(dto).model_dump()}


@router.get("/dashboard")
def get_dashboard(
    current_reseller: Reseller = Depends(get_current_reseller),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    try:
        dto = query_bus.query(GetResellerDashboardQuery(reseller_id=current_reseller.id))
    except ResellerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"data": ResellerMapper.dto_to_dashboard_response(dto).model_dump()}


@router.post("/clients/demo", status_code=201)
def create_demo_account(
    body: CreateDemoAccountRequest,
    reseller: Reseller = Depends(require_active_reseller()),
    container: ResellerContainer = Depends(get_reseller_container),
):
    from src.company_bc.company.application.commands.create_company import CompanyNameExistsError
    from src.reseller_bc.client.application.commands.create_demo_account import CreateDemoAccountCommand
    from src.reseller_bc.client.domain.exceptions import DemoAccountLimitExceededException

    handler = container.create_demo_account_command_handler()
    client_id = str(ulid.new())
    try:
        handler.handle(CreateDemoAccountCommand(
            id=client_id,
            reseller_id=reseller.id,
            company_name=body.company_name,
            admin_email=body.admin_email,
        ))
    except DemoAccountLimitExceededException as e:
        raise HTTPException(status_code=429, detail=str(e))
    except CompanyNameExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return {"data": ResellerClientMapper.demo_dto_to_response(handler.result).model_dump()}


@router.post("/clients/account", status_code=201)
def create_client_account(
    body: CreateClientAccountRequest,
    reseller: Reseller = Depends(require_active_reseller()),
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    from src.company_bc.company.application.commands.create_company import (
        CompanyNameExistsError,
        DomainAlreadyTakenError,
        UserAlreadyExistsError,
    )
    from src.reseller_bc.client.application.commands.create_client_account import CreateClientAccountCommand
    from src.reseller_bc.client.application.queries.list_reseller_clients import ListResellerClientsQuery
    from src.reseller_bc.client.domain.exceptions import CompanyAlreadyLinkedToResellerException

    client_id = str(ulid.new())
    try:
        cmd_bus.dispatch(CreateClientAccountCommand(
            id=client_id,
            reseller_id=reseller.id,
            company_name=body.company_name,
            admin_email=body.admin_email,
        ))
    except CompanyNameExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except DomainAlreadyTakenError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except CompanyAlreadyLinkedToResellerException as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Query back the created client for response
    dto = query_bus.query(ListResellerClientsQuery(
        reseller_id=reseller.id, offset=0, limit=1,
    ))
    if dto.items:
        return {"data": ResellerClientMapper.dto_to_response(dto.items[0]).model_dump()}
    return {"data": {}}


@router.get("/clients")
def list_clients(
    offset: int = QueryParam(0, ge=0),
    limit: int = QueryParam(50, ge=1, le=100),
    reseller: Reseller = Depends(get_current_reseller),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    from src.reseller_bc.client.application.queries.list_reseller_clients import ListResellerClientsQuery

    dto = query_bus.query(ListResellerClientsQuery(
        reseller_id=reseller.id,
        offset=offset,
        limit=limit,
    ))
    return {"data": ResellerClientMapper.dto_to_list_response(dto).model_dump()}


@router.get("/commissions")
def list_commissions(
    offset: int = QueryParam(0, ge=0),
    limit: int = QueryParam(50, ge=1, le=100),
    reseller: Reseller = Depends(get_current_reseller),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    from src.reseller_bc.commission.application.queries.list_commissions import ListCommissionsQuery

    dto = query_bus.query(ListCommissionsQuery(
        reseller_id=reseller.id, offset=offset, limit=limit,
    ))
    return {"data": CommissionMapper.dto_to_list_response(dto).model_dump()}


@router.post("/payouts", status_code=201)
def request_payout(
    reseller: Reseller = Depends(require_active_reseller()),
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    from src.reseller_bc.payout.application.commands.request_payout import RequestPayoutCommand
    from src.reseller_bc.payout.application.queries.list_payouts import ListPayoutsQuery
    from src.reseller_bc.payout.domain.exceptions import (
        InsufficientBalanceException,
        PayoutAlreadyPendingException,
    )

    payout_id = str(ulid.new())
    try:
        cmd_bus.dispatch(RequestPayoutCommand(id=payout_id, reseller_id=reseller.id))
    except InsufficientBalanceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PayoutAlreadyPendingException as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Return created payout
    dto = query_bus.query(ListPayoutsQuery(reseller_id=reseller.id, offset=0, limit=1))
    if dto.items:
        return {"data": PayoutMapper.dto_to_response(dto.items[0]).model_dump()}
    return {"data": {}}


@router.get("/payouts")
def list_payouts(
    offset: int = QueryParam(0, ge=0),
    limit: int = QueryParam(50, ge=1, le=100),
    reseller: Reseller = Depends(get_current_reseller),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    from src.reseller_bc.payout.application.queries.list_payouts import ListPayoutsQuery

    dto = query_bus.query(ListPayoutsQuery(
        reseller_id=reseller.id, offset=offset, limit=limit,
    ))
    return {"data": PayoutMapper.dto_to_list_response(dto).model_dump()}


# ── Invitation endpoints ───────────────────────────────────────────


@router.post("/invitations", status_code=201)
def create_invitation(
    body: CreateInvitationRequest,
    reseller: Reseller = Depends(require_active_reseller()),
    container: ResellerContainer = Depends(get_reseller_container),
):
    from src.reseller_bc.invitation.application.commands.create_invitation import (
        CreateInvitationCommand,
    )
    from src.reseller_bc.invitation.domain.exceptions import (
        InvitationAlreadyExistsException,
        InvitationLimitExceededException,
    )

    handler = container.create_invitation_command_handler()
    try:
        handler.handle(CreateInvitationCommand(
            reseller_id=reseller.id,
            email=body.email,
        ))
    except InvitationLimitExceededException as e:
        raise HTTPException(status_code=429, detail=str(e))
    except InvitationAlreadyExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))

    from src.reseller_bc.invitation.application.dtos import InvitationDto

    return {"data": InvitationMapper.dto_to_response(
        InvitationDto.from_entity(handler.result)
    ).model_dump()}


@router.get("/invitations")
def list_invitations(
    offset: int = QueryParam(0, ge=0),
    limit: int = QueryParam(50, ge=1, le=100),
    reseller: Reseller = Depends(get_current_reseller),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    from src.reseller_bc.invitation.application.queries.list_invitations import (
        ListInvitationsQuery,
    )

    dto = query_bus.query(ListInvitationsQuery(
        reseller_id=reseller.id, offset=offset, limit=limit,
    ))
    return {"data": InvitationMapper.dto_to_list_response(dto).model_dump()}


@router.delete("/invitations/{invitation_id}", status_code=200)
def cancel_invitation(
    invitation_id: str,
    reseller: Reseller = Depends(require_active_reseller()),
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
):
    from src.reseller_bc.invitation.application.commands.cancel_invitation import (
        CancelInvitationCommand,
    )

    cmd_bus.dispatch(CancelInvitationCommand(
        invitation_id=invitation_id,
        reseller_id=reseller.id,
    ))
    return {"message": "Invitation cancelled"}
