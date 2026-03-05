from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import ulid

from src.reseller_bc.invitation.domain.enums import InvitationStatus


@dataclass
class ResellerInvitation:
    id: str
    reseller_id: str
    email: str
    status: InvitationStatus
    expires_at: datetime
    created_at: Optional[datetime]

    @classmethod
    def create(
        cls,
        reseller_id: str,
        email: str,
        id: Optional[str] = None,
    ) -> "ResellerInvitation":
        now = datetime.utcnow()
        return cls(
            id=id or str(ulid.new()),
            reseller_id=reseller_id,
            email=email.lower().strip(),
            status=InvitationStatus.PENDING,
            expires_at=now + timedelta(hours=72),
            created_at=now,
        )
