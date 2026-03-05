from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.reseller_bc.invitation.domain.entities import ResellerInvitation


@dataclass
class InvitationDto:
    id: str
    reseller_id: str
    email: str
    status: str
    expires_at: datetime
    created_at: Optional[datetime]

    @classmethod
    def from_entity(cls, invitation: ResellerInvitation) -> "InvitationDto":
        return cls(
            id=invitation.id,
            reseller_id=invitation.reseller_id,
            email=invitation.email,
            status=invitation.status.value,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )


@dataclass
class InvitationListDto:
    items: list[InvitationDto]
    total: int
