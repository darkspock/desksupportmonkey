from abc import ABC, abstractmethod
from typing import Optional

from src.support_bc.ticket.domain.entities import SupportTicket, TicketMessage


class SupportTicketRepositoryInterface(ABC):

    @abstractmethod
    def save(self, ticket: SupportTicket) -> SupportTicket:
        """Insert or update. On insert, assigns reference via sequence."""
        ...

    @abstractmethod
    def find_by_id(self, ticket_id: str, company_id: str) -> Optional[SupportTicket]:
        ...

    @abstractmethod
    def find_by_id_any_company(self, ticket_id: str) -> Optional[SupportTicket]:
        """For super admin — no company scoping."""
        ...

    @abstractmethod
    def find_all(
        self,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        company_id: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> tuple[list[SupportTicket], int]:
        """List all tickets (super admin). Paginated with filters."""
        ...

    @abstractmethod
    def find_by_company(
        self,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> tuple[list[SupportTicket], int]:
        """List tickets for a company. Paginated with filters."""
        ...

    @abstractmethod
    def find_by_created_by(
        self,
        user_id: str,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str] = None,
    ) -> tuple[list[SupportTicket], int]:
        """List tickets created by user. Paginated."""
        ...

    @abstractmethod
    def find_resolved_older_than_days(self, days: int) -> list[SupportTicket]:
        """For auto-close: resolved tickets older than N days."""
        ...

    @abstractmethod
    def find_stale_older_than_days(self, days: int) -> list[SupportTicket]:
        """For auto-close: active tickets with updated_at older than N days."""
        ...

    @abstractmethod
    def save_message(self, message: TicketMessage) -> TicketMessage:
        ...

    @abstractmethod
    def find_messages(self, ticket_id: str) -> list[TicketMessage]:
        """Ordered by created_at ASC."""
        ...

    @abstractmethod
    def has_unread_platform_messages(
        self, ticket_id: str, last_read_at: Optional[str] = None
    ) -> bool:
        """Check if there are platform messages newer than the user's last visit."""
        ...

    @abstractmethod
    def count_by_status(self) -> dict[str, int]:
        """For super admin dashboard stats."""
        ...

    @abstractmethod
    def get_avg_satisfaction(self) -> Optional[float]:
        """Average satisfaction rating across all rated tickets."""
        ...
