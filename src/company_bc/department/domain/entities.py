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
    manager_user_id: Optional[str] = None
    priority_weight: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(cls, company_id: str, name: str, id: Optional[str] = None) -> "Department":
        if not name or not name.strip():
            raise ValueError("Department name is required")
        return cls(
            id=id or str(ulid.new()),
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

    def assign_manager(self, user_id: str) -> None:
        self.manager_user_id = user_id

    def remove_manager(self) -> None:
        self.manager_user_id = None

    def set_priority_weight(self, weight: int) -> None:
        if weight < -1 or weight > 2:
            raise ValueError("priority_weight must be between -1 and 2")
        self.priority_weight = weight
