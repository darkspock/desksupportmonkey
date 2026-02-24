from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

import ulid

from src.risk_bc.risk.domain.enums import (
    MitigationStatus,
    ReviewCadence,
    RiskCategory,
    RiskHistoryEventType,
    RiskLevel,
    RiskLinkType,
    RiskStatus,
    RiskTreatment,
    VALID_STATUS_TRANSITIONS,
    calculate_risk_level,
)
from src.risk_bc.risk.domain.exceptions import (
    InvalidStatusTransitionError,
    RiskClosedError,
)


@dataclass
class Risk:
    id: str
    company_id: str
    title: str
    description: str
    category: RiskCategory
    status: RiskStatus
    created_by: str
    likelihood: Optional[int] = None
    impact: Optional[int] = None
    risk_level: Optional[RiskLevel] = None
    treatment: Optional[RiskTreatment] = None
    review_cadence: Optional[ReviewCadence] = None
    next_review_at: Optional[datetime] = None
    owner_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        title: str,
        description: str,
        category: RiskCategory,
        created_by: str,
        owner_id: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "Risk":
        if not title or not title.strip():
            raise ValueError("Title is required")
        if not description or not description.strip():
            raise ValueError("Description is required")
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            title=title.strip(),
            description=description.strip(),
            category=category,
            status=RiskStatus.OPEN,
            created_by=created_by,
            owner_id=owner_id,
        )

    def assess(self, likelihood: int, impact: int) -> None:
        if self.status == RiskStatus.CLOSED:
            raise RiskClosedError()
        level = calculate_risk_level(likelihood, impact)
        self.likelihood = likelihood
        self.impact = impact
        self.risk_level = level

    def change_status(self, new_status: RiskStatus) -> None:
        valid_targets = VALID_STATUS_TRANSITIONS.get(self.status, [])
        if new_status not in valid_targets:
            raise InvalidStatusTransitionError(self.status.value, new_status.value)
        self.status = new_status

    def set_treatment(self, treatment: RiskTreatment) -> None:
        if self.status == RiskStatus.CLOSED:
            raise RiskClosedError()
        self.treatment = treatment

    def update_details(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[RiskCategory] = None,
        owner_id: Optional[str] = None,
        review_cadence: Optional[ReviewCadence] = None,
    ) -> None:
        if self.status == RiskStatus.CLOSED:
            raise RiskClosedError()
        if title is not None:
            if not title.strip():
                raise ValueError("Title cannot be empty")
            self.title = title.strip()
        if description is not None:
            if not description.strip():
                raise ValueError("Description cannot be empty")
            self.description = description.strip()
        if category is not None:
            self.category = category
        if owner_id is not None:
            self.owner_id = owner_id
        if review_cadence is not None:
            self.review_cadence = review_cadence


@dataclass
class MitigationPlan:
    id: str
    risk_id: str
    description: str
    status: MitigationStatus
    owner_id: Optional[str] = None
    target_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        risk_id: str,
        description: str,
        owner_id: Optional[str] = None,
        target_date: Optional[date] = None,
        id: Optional[str] = None,
    ) -> "MitigationPlan":
        if not description or not description.strip():
            raise ValueError("Mitigation description is required")
        return cls(
            id=id or str(ulid.new()),
            risk_id=risk_id,
            description=description.strip(),
            status=MitigationStatus.OPEN,
            owner_id=owner_id,
            target_date=target_date,
        )

    def update_status(self, new_status: MitigationStatus) -> None:
        self.status = new_status


@dataclass
class RiskLink:
    id: str
    risk_id: str
    link_type: RiskLinkType
    link_id: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        risk_id: str,
        link_type: RiskLinkType,
        link_id: str,
        id: Optional[str] = None,
    ) -> "RiskLink":
        return cls(
            id=id or str(ulid.new()),
            risk_id=risk_id,
            link_type=link_type,
            link_id=link_id,
        )


@dataclass
class RiskHistory:
    id: str
    risk_id: str
    event_type: RiskHistoryEventType
    description: str
    actor_id: str
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        risk_id: str,
        event_type: RiskHistoryEventType,
        description: str,
        actor_id: str,
        metadata: Optional[dict] = None,
    ) -> "RiskHistory":
        return cls(
            id=str(ulid.new()),
            risk_id=risk_id,
            event_type=event_type,
            description=description,
            actor_id=actor_id,
            metadata=metadata,
        )
