from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid


@dataclass
class Department:
    id: str
    company_id: str
    name: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(cls, company_id: str, name: str) -> "Department":
        if not name or not name.strip():
            raise ValueError("Department name is required")
        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            name=name.strip(),
            is_active=True,
        )

    def deactivate(self) -> None:
        self.is_active = False

    def update_name(self, name: str) -> None:
        if not name or not name.strip():
            raise ValueError("Department name is required")
        self.name = name.strip()
