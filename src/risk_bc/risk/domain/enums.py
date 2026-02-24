from enum import Enum


class RiskCategory(str, Enum):
    OPERATIONAL = "operational"
    CYBER = "cyber"
    COMPLIANCE = "compliance"
    THIRD_PARTY = "third_party"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    CLOSED = "closed"


class RiskTreatment(str, Enum):
    MITIGATE = "mitigate"
    ACCEPT = "accept"
    TRANSFER = "transfer"
    AVOID = "avoid"


class ReviewCadence(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class MitigationStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RiskLinkType(str, Enum):
    ASSET = "asset"
    DEPARTMENT = "department"
    VENDOR = "vendor"


class RiskHistoryEventType(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    SCORE_CHANGED = "score_changed"
    STATUS_CHANGED = "status_changed"
    TREATMENT_CHANGED = "treatment_changed"
    REVIEW_COMPLETED = "review_completed"
    MITIGATION_ADDED = "mitigation_added"
    MITIGATION_UPDATED = "mitigation_updated"
    MITIGATION_DELETED = "mitigation_deleted"
    LINK_ADDED = "link_added"
    LINK_REMOVED = "link_removed"
    OWNER_CHANGED = "owner_changed"


VALID_STATUS_TRANSITIONS: dict[RiskStatus, list[RiskStatus]] = {
    RiskStatus.OPEN: [RiskStatus.UNDER_REVIEW, RiskStatus.ACCEPTED, RiskStatus.CLOSED],
    RiskStatus.UNDER_REVIEW: [
        RiskStatus.OPEN,
        RiskStatus.MITIGATED,
        RiskStatus.ACCEPTED,
        RiskStatus.CLOSED,
    ],
    RiskStatus.MITIGATED: [RiskStatus.OPEN, RiskStatus.CLOSED],
    RiskStatus.ACCEPTED: [RiskStatus.OPEN, RiskStatus.CLOSED],
    RiskStatus.CLOSED: [RiskStatus.OPEN],
}


RISK_LEVEL_MATRIX: dict[tuple[int, int], RiskLevel] = {
    (1, 1): RiskLevel.LOW,
    (1, 2): RiskLevel.LOW,
    (1, 3): RiskLevel.LOW,
    (1, 4): RiskLevel.MEDIUM,
    (1, 5): RiskLevel.MEDIUM,
    (2, 1): RiskLevel.LOW,
    (2, 2): RiskLevel.LOW,
    (2, 3): RiskLevel.MEDIUM,
    (2, 4): RiskLevel.MEDIUM,
    (2, 5): RiskLevel.HIGH,
    (3, 1): RiskLevel.LOW,
    (3, 2): RiskLevel.MEDIUM,
    (3, 3): RiskLevel.MEDIUM,
    (3, 4): RiskLevel.HIGH,
    (3, 5): RiskLevel.HIGH,
    (4, 1): RiskLevel.MEDIUM,
    (4, 2): RiskLevel.MEDIUM,
    (4, 3): RiskLevel.HIGH,
    (4, 4): RiskLevel.HIGH,
    (4, 5): RiskLevel.CRITICAL,
    (5, 1): RiskLevel.MEDIUM,
    (5, 2): RiskLevel.HIGH,
    (5, 3): RiskLevel.HIGH,
    (5, 4): RiskLevel.CRITICAL,
    (5, 5): RiskLevel.CRITICAL,
}


def calculate_risk_level(likelihood: int, impact: int) -> RiskLevel:
    if not (1 <= likelihood <= 5):
        raise ValueError(f"Likelihood must be between 1 and 5, got {likelihood}")
    if not (1 <= impact <= 5):
        raise ValueError(f"Impact must be between 1 and 5, got {impact}")
    return RISK_LEVEL_MATRIX[(likelihood, impact)]
