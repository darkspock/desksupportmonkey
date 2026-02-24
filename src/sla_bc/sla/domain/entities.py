from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import ulid

from src.sla_bc.sla.domain.enums import SlaBreachType
from src.sla_bc.sla.domain.exceptions import InvalidSlaTargetsError


@dataclass
class SlaPolicy:
    id: str
    company_id: str
    name: str
    priority: str
    request_type: Optional[str]
    response_time_hours: float
    resolution_time_hours: float
    warning_threshold_pct: int
    escalate_on_breach: bool
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        name: str,
        priority: str,
        response_time_hours: float,
        resolution_time_hours: float,
        request_type: Optional[str] = None,
        warning_threshold_pct: int = 75,
        escalate_on_breach: bool = False,
    ) -> "SlaPolicy":
        if response_time_hours >= resolution_time_hours:
            raise InvalidSlaTargetsError()
        if response_time_hours <= 0 or resolution_time_hours <= 0:
            raise InvalidSlaTargetsError()
        if not (1 <= warning_threshold_pct <= 99):
            raise ValueError("Warning threshold must be between 1 and 99")

        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            name=name.strip(),
            priority=priority,
            request_type=request_type,
            response_time_hours=response_time_hours,
            resolution_time_hours=resolution_time_hours,
            warning_threshold_pct=warning_threshold_pct,
            escalate_on_breach=escalate_on_breach,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    def update(
        self,
        name: Optional[str] = None,
        response_time_hours: Optional[float] = None,
        resolution_time_hours: Optional[float] = None,
        warning_threshold_pct: Optional[int] = None,
        escalate_on_breach: Optional[bool] = None,
    ) -> None:
        if name is not None:
            self.name = name.strip()
        if response_time_hours is not None:
            self.response_time_hours = response_time_hours
        if resolution_time_hours is not None:
            self.resolution_time_hours = resolution_time_hours
        if warning_threshold_pct is not None:
            if not (1 <= warning_threshold_pct <= 99):
                raise ValueError("Warning threshold must be between 1 and 99")
            self.warning_threshold_pct = warning_threshold_pct
        if escalate_on_breach is not None:
            self.escalate_on_breach = escalate_on_breach

        if self.response_time_hours >= self.resolution_time_hours:
            raise InvalidSlaTargetsError()

        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class SlaBreachRecord:
    id: str
    company_id: str
    request_id: str
    policy_id: str
    breach_type: SlaBreachType
    target_hours: float
    actual_hours: float
    escalated: bool
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        request_id: str,
        policy_id: str,
        breach_type: SlaBreachType,
        target_hours: float,
        actual_hours: float,
        escalated: bool = False,
    ) -> "SlaBreachRecord":
        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            request_id=request_id,
            policy_id=policy_id,
            breach_type=breach_type,
            target_hours=target_hours,
            actual_hours=actual_hours,
            escalated=escalated,
            created_at=datetime.now(timezone.utc),
        )
