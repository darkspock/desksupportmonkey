from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import ulid


@dataclass
class Notification:
    id: str
    user_id: str
    company_id: str
    event_type: str
    title: str
    body: str
    data: Optional[dict] = field(default=None)
    is_read: bool = False
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        user_id: str,
        company_id: str,
        event_type: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> "Notification":
        if not title or not title.strip():
            raise ValueError("Title is required")
        if not body or not body.strip():
            raise ValueError("Body is required")
        return cls(
            id=str(ulid.new()),
            user_id=user_id,
            company_id=company_id,
            event_type=event_type,
            title=title.strip(),
            body=body.strip(),
            data=data,
            is_read=False,
        )
