from sqlalchemy.orm import Session

from core.password import PasswordService
from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository


class ResellerContainer:
    """Dependency container for the Reseller bounded context.

    Provides factory methods for all command/query handlers, following the
    naming convention expected by CommandBus and QueryBus:
        RegisterResellerCommand → register_reseller_command_handler()
    """

    def __init__(self, db: Session):
        self._db = db
        self._reseller_repo = ResellerRepository(db)
        self._password_service = PasswordService()
        # Lazy-initialized repos (only created when needed)
        self._client_repo = None
        self._commission_repo = None
        self._payout_repo = None
        self._company_repo = None
        self._invitation_repo = None

    # ── Lazy repo properties ───────────────────────────────────────────

    @property
    def client_repo(self):
        if self._client_repo is None:
            from src.reseller_bc.client.infrastructure.repository import ResellerClientRepository
            self._client_repo = ResellerClientRepository(self._db)
        return self._client_repo

    @property
    def commission_repo(self):
        if self._commission_repo is None:
            from src.reseller_bc.commission.infrastructure.repository import ResellerCommissionRepository
            self._commission_repo = ResellerCommissionRepository(self._db)
        return self._commission_repo

    @property
    def payout_repo(self):
        if self._payout_repo is None:
            from src.reseller_bc.payout.infrastructure.repository import ResellerPayoutRepository
            self._payout_repo = ResellerPayoutRepository(self._db)
        return self._payout_repo

    @property
    def invitation_repo(self):
        if self._invitation_repo is None:
            from src.reseller_bc.invitation.infrastructure.repository import ResellerInvitationRepository
            self._invitation_repo = ResellerInvitationRepository(self._db)
        return self._invitation_repo

    @property
    def company_repo(self):
        if self._company_repo is None:
            from src.company_bc.company.infrastructure.repository import CompanyRepository
            self._company_repo = CompanyRepository(self._db)
        return self._company_repo

    def _build_company_handler(self):
        """Build CreateCompanyCommandHandler with all cross-BC dependencies."""
        from core.config import settings
        from core.email import get_email_service
        from core.stripe_client import StripeClient
        from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository
        from src.auth_bc.user.infrastructure.repository import UserRepository
        from src.asset_bc.asset.infrastructure.repository import AssetRepository
        from src.asset_type_bc.definition.infrastructure.repository import AssetTypeDefinitionRepository
        from src.company_bc.company.application.commands.create_company import CreateCompanyCommandHandler
        from src.maintenance_bc.maintenance_template.infrastructure.repository import MaintenanceTemplateRepository
        from src.workflow_bc.template.infrastructure.repository import WorkflowTemplateRepository

        return CreateCompanyCommandHandler(
            company_repo=self.company_repo,
            user_repo=UserRepository(self._db),
            magic_link_repo=MagicLinkRepository(self._db),
            email_service=get_email_service(),
            stripe_client=StripeClient(
                secret_key=settings.stripe.STRIPE_SECRET_KEY,
                open_source_mode=settings.stripe.OPEN_SOURCE_MODE,
            ),
            asset_repo=AssetRepository(self._db),
            asset_type_repo=AssetTypeDefinitionRepository(self._db),
            workflow_template_repo=WorkflowTemplateRepository(self._db),
            maint_template_repo=MaintenanceTemplateRepository(self._db),
        )

    # ── Command handler providers ──────────────────────────────────────

    def create_reseller_command_handler(self):
        from src.reseller_bc.reseller.application.commands.create_reseller import CreateResellerCommandHandler
        return CreateResellerCommandHandler(repo=self._reseller_repo)

    def update_reseller_command_handler(self):
        from src.reseller_bc.reseller.application.commands.update_reseller import UpdateResellerCommandHandler
        return UpdateResellerCommandHandler(repo=self._reseller_repo)

    def update_reseller_profile_command_handler(self):
        from src.reseller_bc.reseller.application.commands.update_reseller_profile import UpdateResellerProfileCommandHandler
        return UpdateResellerProfileCommandHandler(repo=self._reseller_repo)

    def register_reseller_command_handler(self):
        from src.reseller_bc.reseller.application.commands.register_reseller import RegisterResellerCommandHandler
        return RegisterResellerCommandHandler(
            repo=self._reseller_repo, password_service=self._password_service,
        )

    def register_reseller_o_auth_command_handler(self):
        from src.reseller_bc.reseller.application.commands.register_reseller_oauth import RegisterResellerOAuthCommandHandler
        return RegisterResellerOAuthCommandHandler(repo=self._reseller_repo)

    def approve_reseller_command_handler(self):
        from src.reseller_bc.reseller.application.commands.approve_reseller import ApproveResellerCommandHandler
        return ApproveResellerCommandHandler(repo=self._reseller_repo)

    def reject_reseller_command_handler(self):
        from src.reseller_bc.reseller.application.commands.reject_reseller import RejectResellerCommandHandler
        return RejectResellerCommandHandler(repo=self._reseller_repo)

    def change_reseller_password_command_handler(self):
        from src.reseller_bc.reseller.application.commands.change_password import ChangeResellerPasswordCommandHandler
        return ChangeResellerPasswordCommandHandler(
            repo=self._reseller_repo, password_service=self._password_service,
        )

    def forgot_reseller_password_command_handler(self):
        from src.reseller_bc.reseller.application.commands.forgot_password import ForgotResellerPasswordCommandHandler
        return ForgotResellerPasswordCommandHandler(repo=self._reseller_repo)

    def reset_reseller_password_command_handler(self):
        from src.reseller_bc.reseller.application.commands.reset_password import ResetResellerPasswordCommandHandler
        return ResetResellerPasswordCommandHandler(
            repo=self._reseller_repo, password_service=self._password_service,
        )

    def create_demo_account_command_handler(self):
        from src.auth_bc.user.infrastructure.repository import UserRepository
        from src.reseller_bc.client.application.commands.create_demo_account import CreateDemoAccountCommandHandler
        return CreateDemoAccountCommandHandler(
            client_repo=self.client_repo,
            reseller_repo=self._reseller_repo,
            company_handler=self._build_company_handler(),
            user_repo=UserRepository(self._db),
            session=self._db,
        )

    def create_client_account_command_handler(self):
        from src.reseller_bc.client.application.commands.create_client_account import CreateClientAccountCommandHandler
        return CreateClientAccountCommandHandler(
            client_repo=self.client_repo,
            reseller_repo=self._reseller_repo,
            company_handler=self._build_company_handler(),
        )

    def request_payout_command_handler(self):
        from src.reseller_bc.payout.application.commands.request_payout import RequestPayoutCommandHandler
        return RequestPayoutCommandHandler(
            payout_repo=self.payout_repo,
            commission_repo=self.commission_repo,
            reseller_repo=self._reseller_repo,
        )

    # ── Query handler providers ────────────────────────────────────────

    def get_reseller_by_id_query_handler(self):
        from src.reseller_bc.reseller.application.queries.get_reseller_by_id import GetResellerByIdQueryHandler
        return GetResellerByIdQueryHandler(repo=self._reseller_repo)

    def list_resellers_query_handler(self):
        from src.reseller_bc.reseller.application.queries.list_resellers import ListResellersQueryHandler
        return ListResellersQueryHandler(repo=self._reseller_repo)

    def get_reseller_dashboard_query_handler(self):
        from src.reseller_bc.reseller.application.queries.get_reseller_dashboard import GetResellerDashboardQueryHandler
        return GetResellerDashboardQueryHandler(
            repo=self._reseller_repo,
            client_repo=self.client_repo,
            commission_repo=self.commission_repo,
            payout_repo=self.payout_repo,
        )

    def list_reseller_clients_query_handler(self):
        from src.reseller_bc.client.application.queries.list_reseller_clients import ListResellerClientsQueryHandler
        return ListResellerClientsQueryHandler(
            client_repo=self.client_repo, company_repo=self.company_repo,
        )

    def list_commissions_query_handler(self):
        from src.reseller_bc.commission.application.queries.list_commissions import ListCommissionsQueryHandler
        return ListCommissionsQueryHandler(
            commission_repo=self.commission_repo, company_repo=self.company_repo,
        )

    def list_payouts_query_handler(self):
        from src.reseller_bc.payout.application.queries.list_payouts import ListPayoutsQueryHandler
        return ListPayoutsQueryHandler(
            payout_repo=self.payout_repo, reseller_repo=self._reseller_repo,
        )

    # ── Invitation handler providers ────────────────────────────────────

    def create_invitation_command_handler(self):
        from src.reseller_bc.invitation.application.commands.create_invitation import CreateInvitationCommandHandler
        return CreateInvitationCommandHandler(invitation_repo=self.invitation_repo)

    def cancel_invitation_command_handler(self):
        from src.reseller_bc.invitation.application.commands.cancel_invitation import CancelInvitationCommandHandler
        return CancelInvitationCommandHandler(invitation_repo=self.invitation_repo)

    def claim_invitation_command_handler(self):
        from src.reseller_bc.invitation.application.commands.claim_invitation import ClaimInvitationCommandHandler
        return ClaimInvitationCommandHandler(
            invitation_repo=self.invitation_repo, client_repo=self.client_repo,
        )

    def list_invitations_query_handler(self):
        from src.reseller_bc.invitation.application.queries.list_invitations import ListInvitationsQueryHandler
        return ListInvitationsQueryHandler(invitation_repo=self.invitation_repo)
