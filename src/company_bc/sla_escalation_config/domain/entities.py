from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid


@dataclass
class CompanySlaEscalationConfig:
    id: str
    company_id: str
    enabled: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        enabled: bool = True,
    ) -> "CompanySlaEscalationConfig":
        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            enabled=enabled,
        )
