import logging
from dataclasses import dataclass
from typing import Optional

from core.email import EmailServiceInterface, send_magic_link_email
from core.stripe_client import StripeClient
from src.asset_bc.asset.domain.entities import AssetLocation
from src.asset_bc.asset.domain.enums import SystemLocation
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.asset_type_bc.definition.domain.entities import AssetTypeDefinition
from src.asset_type_bc.definition.domain.repository import (
    AssetTypeDefinitionRepositoryInterface,
)
from src.workflow_bc.template.domain.entities import (
    ChecklistItemDefinition,
    WorkflowTemplate,
)
from src.workflow_bc.template.domain.repository import (
    WorkflowTemplateRepositoryInterface,
)
from src.auth_bc.magic_link.domain.entities import MagicLink
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.company.application.ports import MagicLinkWriter, UserWriter
from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class CompanyNameExistsError(Exception):
    pass


class DomainAlreadyTakenError(Exception):
    def __init__(self, domain: str):
        self.domain = domain
        super().__init__(f"Domain '{domain}' is already associated with another company")


class UserAlreadyExistsError(Exception):
    pass


@dataclass
class CreateCompanyCommand(Command):
    name: str
    email_domains: list[str]
    admin_email: Optional[str] = None
    id: Optional[str] = None


SYSTEM_LOCATION_NAMES: dict[str, str] = {
    SystemLocation.EMPLOYEE.value: "Empleado",
    SystemLocation.IN_TRANSIT.value: "En Tránsito",
    SystemLocation.MAIN_WAREHOUSE.value: "Almacén Principal",
}

DEFAULT_ASSET_TYPES: list[tuple[str, str | None, int]] = [
    ("Laptop", "laptop", 0),
    ("Monitor", "monitor", 1),
    ("Keyboard", "keyboard", 2),
    ("Mouse", "mouse", 3),
    ("Headset", "headset", 4),
    ("Phone", "phone", 5),
    ("Docking Station", "dock", 6),
    ("Other", None, 7),
]

DEFAULT_WORKFLOW_TEMPLATES: list[dict] = [
    {
        "name": "Incident",
        "description": "Report a technical issue or outage",
        "require_all_complete": False,
        "checklist_items": [
            {"title": "Identify root cause", "is_required": True},
            {"title": "Apply fix or workaround", "is_required": True},
            {"title": "Verify resolution with reporter", "is_required": True},
            {"title": "Update documentation", "is_required": False},
        ],
    },
    {
        "name": "New Equipment",
        "description": "Request new hardware or software",
        "require_all_complete": True,
        "checklist_items": [
            {"title": "Verify budget approval", "is_required": True},
            {"title": "Place purchase order", "is_required": True},
            {"title": "Receive and inspect equipment", "is_required": True},
            {"title": "Configure and install", "is_required": True},
            {"title": "Deliver to employee", "is_required": True},
            {"title": "Confirm employee acceptance", "is_required": True},
        ],
    },
    {
        "name": "Employee Onboarding",
        "description": "Set up accounts, equipment, and access for new hire",
        "require_all_complete": True,
        "checklist_items": [
            {"title": "Create user accounts (email, Slack, etc.)", "is_required": True},
            {"title": "Assign laptop and peripherals", "is_required": True},
            {"title": "Set up VPN and network access", "is_required": True},
            {"title": "Grant application permissions", "is_required": True},
            {"title": "Ship equipment to employee", "is_required": True},
            {"title": "Schedule orientation call", "is_required": False},
            {"title": "Add to team channels", "is_required": False},
        ],
    },
    {
        "name": "Employee Offboarding",
        "description": "Revoke access and recover equipment for departing employee",
        "require_all_complete": True,
        "checklist_items": [
            {"title": "Disable email account", "is_required": True},
            {"title": "Revoke VPN and network access", "is_required": True},
            {"title": "Revoke application permissions", "is_required": True},
            {"title": "Wipe company data from devices", "is_required": True},
            {"title": "Collect company equipment", "is_required": True},
            {"title": "Collect badge and physical keys", "is_required": True},
            {"title": "Transfer file ownership", "is_required": False},
        ],
    },
    {
        "name": "Access Request",
        "description": "Request access to systems, applications, or physical spaces",
        "require_all_complete": True,
        "checklist_items": [
            {"title": "Verify manager approval", "is_required": True},
            {"title": "Provision access", "is_required": True},
            {"title": "Confirm access works", "is_required": True},
        ],
    },
]


class CreateCompanyCommandHandler(CommandHandler[CreateCompanyCommand]):
    def __init__(
        self,
        company_repo: CompanyRepositoryInterface,
        user_repo: UserWriter,
        magic_link_repo: MagicLinkWriter,
        email_service: EmailServiceInterface,
        stripe_client: StripeClient,
        asset_repo: Optional[AssetRepositoryInterface] = None,
        asset_type_repo: Optional[AssetTypeDefinitionRepositoryInterface] = None,
        workflow_template_repo: Optional[WorkflowTemplateRepositoryInterface] = None,
    ):
        self.company_repo = company_repo
        self.user_repo = user_repo
        self.magic_link_repo = magic_link_repo
        self.email_service = email_service
        self.stripe_client = stripe_client
        self.asset_repo = asset_repo
        self.asset_type_repo = asset_type_repo
        self.workflow_template_repo = workflow_template_repo

    def handle(self, command: CreateCompanyCommand) -> None:
        # Check name uniqueness
        existing = self.company_repo.find_by_name(command.name)
        if existing:
            raise CompanyNameExistsError("Company with this name already exists")

        # Validate + normalize domains early so uniqueness checks are canonical
        company = Company.create(
            name=command.name, email_domains=command.email_domains, id=command.id,
        )

        # Check domain uniqueness — allow reclaiming if the owning company has no confirmed users
        for domain in company.email_domains:
            owner_id = self.company_repo.find_domain(domain)
            if owner_id:
                if self.user_repo.has_any_verified_user_in_company(owner_id):
                    raise DomainAlreadyTakenError(domain)
                # No confirmed users: delete the unconfirmed company so this registration can proceed
                logger.info(
                    "Reclaiming domain '%s' from unconfirmed company %s", domain, owner_id
                )
                self.user_repo.delete_by_company(owner_id)
                self.company_repo.delete(owner_id)

        self.company_repo.save(company)
        self.company_repo.save_domains(company.id, company.email_domains)

        # Create Stripe customer (no-op if open_source_mode=True)
        customer_id = self.stripe_client.create_customer(
            name=company.name,
            email=command.admin_email or "",
            metadata={"company_id": company.id},
        )
        company.stripe_customer_id = customer_id
        self.company_repo.save(company)

        # Handle initial admin
        if command.admin_email:
            email = command.admin_email.lower().strip()
            existing_user = self.user_repo.find_by_email(email)
            if existing_user:
                raise UserAlreadyExistsError("User with this email already exists")

            user = User.create(
                email=email,
                role=UserRole.ADMIN,
                company_id=company.id,
            )
            self.user_repo.save(user)

            magic_link = MagicLink.create(email)
            self.magic_link_repo.save(magic_link)
            send_magic_link_email(self.email_service, email, magic_link.token)
            logger.info("Initial admin %s created for company %s", email, company.name)

        # Seed system asset locations for the new company
        if self.asset_repo:
            for key, name in SYSTEM_LOCATION_NAMES.items():
                loc = AssetLocation.create(
                    company_id=company.id,
                    name=name,
                    is_system=True,
                    system_key=key,
                )
                self.asset_repo.save_location(loc)
            logger.info("Seeded system locations for company %s", company.id)

        # Seed default asset type definitions
        if self.asset_type_repo:
            for name, icon, sort_order in DEFAULT_ASSET_TYPES:
                at = AssetTypeDefinition.create(
                    company_id=company.id,
                    name=name,
                    icon=icon,
                    sort_order=sort_order,
                )
                self.asset_type_repo.save(at)
            logger.info("Seeded default asset types for company %s", company.id)

        # Seed default workflow templates
        if self.workflow_template_repo:
            for i, spec in enumerate(DEFAULT_WORKFLOW_TEMPLATES):
                template = WorkflowTemplate.create(
                    company_id=company.id,
                    name=spec["name"],
                    description=spec.get("description"),
                    require_all_complete=spec.get("require_all_complete", False),
                    sort_order=i,
                )
                items = []
                for j, item_spec in enumerate(spec.get("checklist_items", [])):
                    items.append(ChecklistItemDefinition.create(
                        template_id=template.id,
                        title=item_spec["title"],
                        is_required=item_spec.get("is_required", True),
                        sort_order=j,
                    ))
                template.set_checklist_items(items)
                self.workflow_template_repo.save(template)
            logger.info("Seeded default workflow templates for company %s", company.id)

        logger.info("Company created: %s (id=%s)", company.name, company.id)
