from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid


@dataclass
class EmployeeRole:
    id: str
    company_id: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        name: str,
        description: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "EmployeeRole":
        if not name or not name.strip():
            raise ValueError("Employee role name is required")
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            name=name.strip(),
            description=description.strip() if description else None,
            is_active=True,
        )

    def update_name(self, name: str) -> None:
        if not name or not name.strip():
            raise ValueError("Employee role name is required")
        self.name = name.strip()

    def update_description(self, description: Optional[str]) -> None:
        self.description = description.strip() if description else None

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True
