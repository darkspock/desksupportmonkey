import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.email import EmailServiceInterface, send_magic_link_email
from src.auth_bc.company_lookup.domain.service import CompanyLookupInterface
from src.auth_bc.magic_link.domain.entities import MagicLink
from src.auth_bc.magic_link.domain.repository import MagicLinkRepositoryInterface

logger = logging.getLogger(__name__)


class InvalidEmailDomainError(Exception):
    pass


class RateLimitExceededError(Exception):
    pass


class CompanyRestrictedError(Exception):
    pass


@dataclass
class CreateMagicLinkCommand:
    email: str


class CreateMagicLinkCommandHandler:
    MAX_LINKS_PER_HOUR = 5

    def __init__(
        self,
        magic_link_repo: MagicLinkRepositoryInterface,
        company_lookup: CompanyLookupInterface,
        email_service: EmailServiceInterface,
    ):
        self.magic_link_repo = magic_link_repo
        self.company_lookup = company_lookup
        self.email_service = email_service

    def handle(self, command: CreateMagicLinkCommand) -> None:
        email = command.email.lower().strip()
        logger.info("Creating magic link for %s", email)

        # Check email domain matches a company (with status awareness)
        result = self.company_lookup.find_company_by_email_domain(email)
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
