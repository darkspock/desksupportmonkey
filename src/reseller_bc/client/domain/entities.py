from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import ulid

from src.reseller_bc.client.domain.enums import ClientSource


@dataclass
class ResellerClient:
    id: str
    reseller_id: str
    company_id: str
    source: ClientSource
    is_demo: bool
    demo_expires_at: Optional[datetime]
    created_at: Optional[datetime]

    @classmethod
    def create(
        cls,
        reseller_id: str,
        company_id: str,
        source: ClientSource,
        is_demo: bool = False,
        id: Optional[str] = None,
    ) -> "ResellerClient":
        now = datetime.utcnow()
        return cls(
            id=id or str(ulid.new()),
            reseller_id=reseller_id,
            company_id=company_id,
            source=source,
            is_demo=is_demo,
            demo_expires_at=now + timedelta(days=14) if is_demo else None,
            created_at=now,
        )
