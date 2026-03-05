from abc import ABC, abstractmethod
from typing import Optional

from src.reseller_bc.invitation.domain.entities import ResellerInvitation


class ResellerInvitationRepositoryInterface(ABC):
    @abstractmethod
    def save(self, invitation: ResellerInvitation) -> None: ...

    @abstractmethod
    def find_pending_by_email(self, email: str) -> Optional[ResellerInvitation]: ...

    @abstractmethod
    def count_pending_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def find_by_reseller_id(self, reseller_id: str, offset: int = 0, limit: int = 50) -> list[ResellerInvitation]: ...

    @abstractmethod
    def count_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def find_expired_pending(self) -> list[ResellerInvitation]: ...

    @abstractmethod
    def cancel_by_id(self, invitation_id: str, reseller_id: str) -> Optional[ResellerInvitation]: ...
