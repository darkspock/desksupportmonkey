# Technical Design: E37 — Risk Register

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-23
**Bounded Context:** `risk_bc`

## 1. Domain Layer

### 1.1 Enums

**File:** `src/risk_bc/risk/domain/enums.py`

```python
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
    RiskStatus.UNDER_REVIEW: [RiskStatus.OPEN, RiskStatus.MITIGATED, RiskStatus.ACCEPTED, RiskStatus.CLOSED],
    RiskStatus.MITIGATED: [RiskStatus.OPEN, RiskStatus.CLOSED],
    RiskStatus.ACCEPTED: [RiskStatus.OPEN, RiskStatus.CLOSED],
    RiskStatus.CLOSED: [RiskStatus.OPEN],
}
```

### 1.2 Risk Level Calculation

```python
RISK_LEVEL_MATRIX: dict[tuple[int, int], RiskLevel] = {
    (1, 1): RiskLevel.LOW, (1, 2): RiskLevel.LOW, (1, 3): RiskLevel.LOW, (1, 4): RiskLevel.MEDIUM, (1, 5): RiskLevel.MEDIUM,
    (2, 1): RiskLevel.LOW, (2, 2): RiskLevel.LOW, (2, 3): RiskLevel.MEDIUM, (2, 4): RiskLevel.MEDIUM, (2, 5): RiskLevel.HIGH,
    (3, 1): RiskLevel.LOW, (3, 2): RiskLevel.MEDIUM, (3, 3): RiskLevel.MEDIUM, (3, 4): RiskLevel.HIGH, (3, 5): RiskLevel.HIGH,
    (4, 1): RiskLevel.MEDIUM, (4, 2): RiskLevel.MEDIUM, (4, 3): RiskLevel.HIGH, (4, 4): RiskLevel.HIGH, (4, 5): RiskLevel.CRITICAL,
    (5, 1): RiskLevel.MEDIUM, (5, 2): RiskLevel.HIGH, (5, 3): RiskLevel.HIGH, (5, 4): RiskLevel.CRITICAL, (5, 5): RiskLevel.CRITICAL,
}

def calculate_risk_level(likelihood: int, impact: int) -> RiskLevel:
    return RISK_LEVEL_MATRIX[(likelihood, impact)]
```

### 1.3 Entities

**File:** `src/risk_bc/risk/domain/entities.py`

```python
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
    def create(cls, ...) -> "Risk": ...
    def assess(self, likelihood: int, impact: int) -> None: ...
    def change_status(self, new_status: RiskStatus) -> None: ...
    def set_treatment(self, treatment: RiskTreatment) -> None: ...
    def update_details(self, ...) -> None: ...

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
    def create(cls, ...) -> "MitigationPlan": ...
    def update_status(self, new_status: MitigationStatus) -> None: ...

@dataclass
class RiskLink:
    id: str
    risk_id: str
    link_type: RiskLinkType
    link_id: str
    created_at: Optional[datetime] = None

@dataclass
class RiskHistory:
    id: str
    risk_id: str
    event_type: RiskHistoryEventType
    description: str
    actor_id: str
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None
```

### 1.4 Repository Interface

**File:** `src/risk_bc/risk/domain/repository.py`

```python
class RiskRepositoryInterface(ABC):
    @abstractmethod
    def save(self, risk: Risk) -> None: ...
    @abstractmethod
    def find_by_id(self, risk_id: str, company_id: str) -> Optional[Risk]: ...
    @abstractmethod
    def find_all(self, company_id: str, filters: dict) -> tuple[list[Risk], int]: ...
    @abstractmethod
    def delete(self, risk_id: str, company_id: str) -> None: ...
    @abstractmethod
    def add_history(self, entry: RiskHistory) -> None: ...
    @abstractmethod
    def get_history(self, risk_id: str) -> list[RiskHistory]: ...
    @abstractmethod
    def save_mitigation(self, plan: MitigationPlan) -> None: ...
    @abstractmethod
    def find_mitigation_by_id(self, mitigation_id: str, risk_id: str) -> Optional[MitigationPlan]: ...
    @abstractmethod
    def get_mitigations(self, risk_id: str) -> list[MitigationPlan]: ...
    @abstractmethod
    def delete_mitigation(self, mitigation_id: str, risk_id: str) -> None: ...
    @abstractmethod
    def add_link(self, link: RiskLink) -> None: ...
    @abstractmethod
    def get_links(self, risk_id: str) -> list[RiskLink]: ...
    @abstractmethod
    def delete_link(self, link_id: str, risk_id: str) -> None: ...
    @abstractmethod
    def get_dashboard_stats(self, company_id: str) -> dict: ...
    @abstractmethod
    def find_overdue_reviews(self, company_id: Optional[str] = None) -> list[Risk]: ...
```

### 1.5 Domain Exceptions

**File:** `src/risk_bc/risk/domain/exceptions.py`

```python
class RiskNotFoundError(Exception): ...
class InvalidStatusTransitionError(Exception): ...
class RiskClosedError(Exception): ...
class InvalidScoreError(Exception): ...
class MitigationNotFoundError(Exception): ...
class LinkNotFoundError(Exception): ...
class DuplicateLinkError(Exception): ...
```

## 2. Application Layer

### 2.1 Commands (F0)

| File | Command | Handler |
|------|---------|---------|
| `create_risk.py` | CreateRiskCommand | Creates Risk entity, saves, adds history |
| `update_risk.py` | UpdateRiskCommand | Updates risk details, adds history |
| `assess_risk.py` | AssessRiskCommand | Sets likelihood+impact, calculates level, adds history |
| `change_risk_status.py` | ChangeRiskStatusCommand | Validates transition, changes status, adds history |
| `set_treatment.py` | SetTreatmentCommand | Sets treatment option, adds history |
| `delete_risk.py` | DeleteRiskCommand | Deletes risk |

### 2.2 Commands (F1)

| File | Command | Handler |
|------|---------|---------|
| `add_mitigation.py` | AddMitigationCommand | Creates MitigationPlan, adds history |
| `update_mitigation.py` | UpdateMitigationCommand | Updates mitigation status/details, adds history |
| `delete_mitigation.py` | DeleteMitigationCommand | Deletes mitigation, adds history |
| `add_link.py` | AddLinkCommand | Creates RiskLink, adds history |
| `remove_link.py` | RemoveLinkCommand | Deletes link, adds history |

### 2.3 Queries (F0)

| File | Query | Returns |
|------|-------|---------|
| `list_risks.py` | ListRisksQuery | tuple[list[RiskListDto], int] |
| `get_risk_detail.py` | GetRiskDetailQuery | RiskDetailDto |

### 2.4 Queries (F1)

| File | Query | Returns |
|------|-------|---------|
| `get_risk_history.py` | GetRiskHistoryQuery | list[RiskHistoryDto] |

### 2.5 Queries (F3)

| File | Query | Returns |
|------|-------|---------|
| `get_dashboard.py` | GetRiskDashboardQuery | RiskDashboardDto |

### 2.6 DTOs

```python
@dataclass
class RiskListDto:
    id: str
    title: str
    category: str
    status: str
    risk_level: Optional[str]
    likelihood: Optional[int]
    impact: Optional[int]
    treatment: Optional[str]
    owner_id: Optional[str]
    owner_name: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

@dataclass
class RiskDetailDto:
    id: str
    title: str
    description: str
    category: str
    status: str
    likelihood: Optional[int]
    impact: Optional[int]
    risk_level: Optional[str]
    treatment: Optional[str]
    review_cadence: Optional[str]
    next_review_at: Optional[datetime]
    owner_id: Optional[str]
    owner_name: Optional[str]
    created_by: str
    created_by_name: Optional[str]
    mitigations: list[MitigationDto]
    links: list[RiskLinkDto]
    history: list[RiskHistoryDto]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

@dataclass
class MitigationDto:
    id: str
    description: str
    status: str
    owner_id: Optional[str]
    owner_name: Optional[str]
    target_date: Optional[date]
    created_at: Optional[datetime]

@dataclass
class RiskLinkDto:
    id: str
    link_type: str
    link_id: str
    link_name: Optional[str]

@dataclass
class RiskHistoryDto:
    id: str
    event_type: str
    description: str
    actor_id: str
    actor_name: Optional[str]
    metadata: Optional[dict]
    created_at: Optional[datetime]

@dataclass
class RiskDashboardDto:
    total_risks: int
    open_risks: int
    mitigated_risks: int
    accepted_risks: int
    by_level: dict[str, int]       # {low: N, medium: N, high: N, critical: N}
    by_category: dict[str, int]    # {operational: N, cyber: N, ...}
    heat_map: list[dict]           # [{likelihood: 1, impact: 1, count: N}, ...]
    overdue_reviews: int
    recent_risks: list[RiskListDto]
```

## 3. Infrastructure Layer

### 3.1 ORM Models

**File:** `src/risk_bc/risk/infrastructure/models.py`

4 models: `RiskModel`, `MitigationPlanModel`, `RiskLinkModel`, `RiskHistoryModel`

Key indexes:
- `ix_risks_company_status` (company_id, status)
- `ix_risks_company_level` (company_id, risk_level)
- `ix_risks_company_category` (company_id, category)
- `ix_risks_next_review` (next_review_at)
- `ix_mitigation_plans_risk_id` (risk_id)
- `ix_risk_links_risk_id` (risk_id)
- `uq_risk_links_risk_type_entity` (risk_id, link_type, link_id)
- `ix_risk_history_risk_id` (risk_id)

### 3.2 Database Migration

**File:** `alembic/versions/y2a3b4c5d6e7_create_risk_tables.py`

Tables:
1. `risks` — Main risk entries
2. `mitigation_plans` — Mitigation plans per risk
3. `risk_links` — Cross-BC links to assets/departments/vendors
4. `risk_history` — Audit trail

## 4. HTTP Layer

### 4.1 Router Organization

```
adapters/http/api/risks/
├── __init__.py
├── routers.py
├── schemas.py
└── dependencies.py
```

### 4.2 Endpoint Summary

| Method | Path | Role | Feature |
|--------|------|------|---------|
| POST | /api/v1/risks | admin | F0 |
| GET | /api/v1/risks | technician+ | F0 |
| GET | /api/v1/risks/dashboard | technician+ | F3 |
| GET | /api/v1/risks/:id | technician+ | F0 |
| PUT | /api/v1/risks/:id | admin | F0 |
| DELETE | /api/v1/risks/:id | admin | F0 |
| POST | /api/v1/risks/:id/assess | admin | F0 |
| POST | /api/v1/risks/:id/treatment | admin | F0 |
| POST | /api/v1/risks/:id/status | admin | F0 |
| GET | /api/v1/risks/:id/history | technician+ | F0 |
| POST | /api/v1/risks/:id/mitigations | admin | F1 |
| PUT | /api/v1/risks/:id/mitigations/:mid | technician+ | F1 |
| DELETE | /api/v1/risks/:id/mitigations/:mid | admin | F1 |
| POST | /api/v1/risks/:id/links | admin | F1 |
| DELETE | /api/v1/risks/:id/links/:lid | admin | F1 |
| POST | /api/v1/risks/export | admin | F2 |

## 5. Frontend Architecture

### 5.1 Pages

| Page | Path | Role | Feature |
|------|------|------|---------|
| RiskListPage | /risks | technician+ | F0 |
| RiskDetailPage | /risks/:id | technician+ | F0 |
| CreateRiskPage | /risks/new | admin | F0 |
| EditRiskPage | /risks/:id/edit | admin | F0 |
| RiskDashboardPage | /risks/dashboard | technician+ | F3 |

### 5.2 Sidebar Navigation

Under "Security" section (with existing incidents):
- Risk Register → /risks (technician+)
- Risk Dashboard → /risks/dashboard (technician+)

## 6. Testing Strategy

### 6.1 Unit Tests

| Test File | What It Tests |
|-----------|---------------|
| `tests/unit/risk_bc/risk/domain/test_entities.py` | Entity creation, scoring, state transitions |
| `tests/unit/risk_bc/risk/application/commands/test_create_risk.py` | Create command handler |
| `tests/unit/risk_bc/risk/application/commands/test_assess_risk.py` | Assess command handler |
| `tests/unit/risk_bc/risk/application/commands/test_change_status.py` | Status transition handler |
| `tests/unit/risk_bc/risk/application/queries/test_list_risks.py` | List query handler |
| `tests/unit/risk_bc/risk/application/queries/test_get_risk_detail.py` | Detail query handler |

### 6.2 Integration Tests

**File:** `tests/integration/test_risks_endpoints.py`

Coverage: All CRUD operations, scoring, status transitions, mitigations, links, history, dashboard, authorization.

## 7. Implementation Order

**Phase 1: F0 — Risk Foundation** (Domain → Infra → App → HTTP → Tests → FE)
**Phase 2: F1 — Mitigations & Links** (Commands → HTTP → Tests → FE)
**Phase 3: F2 — Reviews, Alerts & Export** (Celery → Export → Tests → FE)
**Phase 4: F3 — Risk Dashboard** (Query → HTTP → Tests → FE)

## 8. Collateral Changes

| File | Component | Change | Feature |
|------|-----------|--------|---------|
| `app.py` | Router registration | Add risks router | F0 |
| `web/app/src/router.tsx` | Routes | Add risk pages | F0 |
| `web/app/src/components/layout/Sidebar.tsx` | Navigation | Add risk entries | F0 |
| `web/app/src/locales/en.ts` | i18n | Risk translations | F0 |
| `web/app/src/locales/es.ts` | i18n | Risk translations | F0 |
| `web/app/src/types/index.ts` | Types | Risk interfaces | F0 |
| `core/celery.py` | Beat schedule | Review reminder task | F2 |
| `core/tasks/__init__.py` | Imports | Risk tasks | F2 |
