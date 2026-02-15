from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    company_id: str
    actor_id: str
    payload: dict
    title: str
    body: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
