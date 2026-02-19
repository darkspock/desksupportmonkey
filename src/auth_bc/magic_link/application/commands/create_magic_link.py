import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.email import EmailServiceInterface, send_magic_link_email
from src.auth_bc.company_lookup.domain.service import CompanyLookupInterface
from src.auth_bc.magic_link.domain.entities import MagicLink
from src.auth_bc.magic_link.domain.repository import MagicLinkRepositoryInterface
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class InvalidEmailDomainError(Exception):
    pass


class RateLimitExceededError(Exception):
    pass


class CompanyRestrictedError(Exception):
    pass


@dataclass
class CreateMagicLinkCommand(Command):
    email: str


class CreateMagicLinkCommandHandler(CommandHandler[CreateMagicLinkCommand]):
    MAX_LINKS_PER_HOUR = 5

    def __init__(
        self,
        magic_link_repo: MagicLinkRepositoryInterface,
        company_lookup: CompanyLookupInterface,
        email_service: EmailServiceInterface,
        user_repo: UserRepositoryInterface | None = None,
    ):
        self.magic_link_repo = magic_link_repo
        self.company_lookup = company_lookup
        self.email_service = email_service
        self.user_repo = user_repo

    def handle(self, command: CreateMagicLinkCommand) -> None:
        email = command.email.lower().strip()
        logger.info("Creating magic link for %s", email)

        # Check email domain matches a company (with status awareness)
        result = self.company_lookup.find_company_by_email_domain(email)
        if result is None:
            # Allow existing users (e.g. admins registered with non-company domains)
            if self.user_repo:
                existing_user = self.user_repo.find_by_email(email)
                if existing_user and existing_user.is_active:
                    result = (existing_user.company_id or "", True)
            if result is None:
                raise InvalidEmailDomainError("Only corporate email addresses are allowed")

        company_id, is_active = result
        if not is_active:
            raise CompanyRestrictedError("Company access is currently restricted")

        # Check rate limit
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_count = self.magic_link_repo.count_recent_by_email(email, since)
        if recent_count >= self.MAX_LINKS_PER_HOUR:
            raise RateLimitExceededError(
                f"Too many requests. Please wait before requesting another link."
            )

        # Create and save magic link
        magic_link = MagicLink.create(email, ttl_hours=24)
        self.magic_link_repo.save(magic_link)

        # Send email
        send_magic_link_email(self.email_service, email, magic_link.token)
        logger.info("Magic link created and sent for %s", email)
