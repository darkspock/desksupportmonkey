from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import ulid


@dataclass
class CompanyNavConfig:
    id: str
    company_id: str
    hidden_nav_items: Dict[str, List[str]] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        hidden_nav_items: Optional[Dict[str, List[str]]] = None,
        id: Optional[str] = None,
    ) -> "CompanyNavConfig":
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            hidden_nav_items=hidden_nav_items or {},
        )
