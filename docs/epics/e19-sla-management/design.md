# E19: SLA Management — Technical Design

**Date:** 2026-02-23
**Requirements:** [requirements.md](requirements.md)

## Bounded Context

New bounded context: `sla_bc` under `src/sla_bc/sla/`.

Rationale: SLA policies are a cross-cutting concern that monitors request lifecycle but has its own entities (policies, breach records), its own CRUD, and its own periodic task. Keeping it separate from `request_bc` prevents coupling and allows independent evolution.

## Domain Layer

### Entities

```
src/sla_bc/sla/domain/
  entities.py      — SlaPolicy, SlaBreachRecord
  enums.py         — SlaBreachType
  exceptions.py    — SlaPolicyNotFoundError, DuplicateSlaPolicyError, InvalidSlaTargetsError
  repository.py    — SlaRepositoryInterface
```

#### SlaPolicy
```python
@dataclass
class SlaPolicy:
    id: str
    company_id: str
    name: str
    priority: str           # urgent/high/medium/low
    request_type: str | None  # null = default for priority
    response_time_hours: float
    resolution_time_hours: float
    warning_threshold_pct: int  # default 75
    escalate_on_breach: bool    # default False
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, ...) -> "SlaPolicy":
        if response_time_hours >= resolution_time_hours:
            raise InvalidSlaTargetsError(...)
        ...

    def update(self, ...) -> None:
        ...

    def deactivate(self) -> None:
        self.is_active = False
```

#### SlaBreachRecord
```python
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
    created_at: datetime

    @classmethod
    def create(cls, ...) -> "SlaBreachRecord":
        ...
```

### Repository Interface

```python
class SlaRepositoryInterface(ABC):
    # Policies
    def save_policy(self, policy: SlaPolicy) -> None
    def find_policy_by_id(self, policy_id: str, company_id: str) -> SlaPolicy | None
    def find_policies(self, company_id: str, is_active: bool | None = None) -> list[SlaPolicy]
    def find_policy_for_request(self, company_id: str, priority: str, request_type: str | None) -> SlaPolicy | None
    def delete_policy(self, policy_id: str, company_id: str) -> None

    # Breach Records
    def save_breach(self, breach: SlaBreachRecord) -> None
    def find_breaches_for_request(self, request_id: str, company_id: str) -> list[SlaBreachRecord]
    def has_breach_of_type(self, request_id: str, breach_type: str) -> bool
    def find_breaches(self, company_id: str, from_date: datetime | None, to_date: datetime | None, page: int, page_size: int) -> tuple[list[SlaBreachRecord], int]

    # Dashboard queries
    def compliance_stats(self, company_id: str, from_date: datetime, to_date: datetime) -> dict
    def compliance_by_priority(self, company_id: str, from_date: datetime, to_date: datetime) -> list[dict]
    def compliance_by_type(self, company_id: str, from_date: datetime, to_date: datetime) -> list[dict]
    def breach_trend(self, company_id: str, from_date: datetime, to_date: datetime, bucket: str) -> list[dict]
```

## Infrastructure Layer

### ORM Models

```
src/sla_bc/sla/infrastructure/
  models.py       — SlaPolicyModel, SlaBreachRecordModel
  repository.py   — SlaRepository
```

#### SlaPolicyModel
- Table: `sla_policies`
- Unique constraint: `(company_id, priority, request_type)` where `is_active = true`
- Indexes: `(company_id, is_active)`, `(company_id, priority, request_type, is_active)`

#### SlaBreachRecordModel
- Table: `sla_breach_records`
- Indexes: `(company_id, created_at)`, `(request_id)`, `(request_id, breach_type)` unique per breach type per request

### Alembic Migration
- Creates `sla_policies` and `sla_breach_records` tables
- Partial unique index on `sla_policies(company_id, priority, request_type) WHERE is_active = true`

## Application Layer

### Commands

```
src/sla_bc/sla/application/commands/
  create_policy.py     — CreateSlaPolicyCommand + handler
  update_policy.py     — UpdateSlaPolicyCommand + handler
  deactivate_policy.py — DeactivateSlaPolicyCommand + handler
  record_breach.py     — RecordSlaBreachCommand + handler (internal, used by Celery task)
```

### Queries

```
src/sla_bc/sla/application/queries/
  list_policies.py     — ListSlaPoliciesQuery + handler
  get_policy.py        — GetSlaPolicyQuery + handler
  get_request_sla.py   — GetRequestSlaStatusQuery + handler (computes SLA status for a request)
  get_dashboard.py     — GetSlaDashboardQuery + handler (compliance metrics)
```

#### GetRequestSlaStatusQuery
Key query: given a request_id, finds the applicable SLA policy, calculates response/resolution times, and returns:
```python
@dataclass
class SlaStatusDto:
    policy_name: str | None
    response_target_hours: float | None
    resolution_target_hours: float | None
    response_elapsed_hours: float
    resolution_elapsed_hours: float
    response_status: str  # "on_track" | "warning" | "breached" | "met"
    resolution_status: str
    response_remaining_hours: float | None
    resolution_remaining_hours: float | None
```

This requires reading from both `sla_bc` (policy) and `request_bc` (request data). The query handler will receive the request repository as a dependency to read request data.

## HTTP Layer

```
adapters/http/api/sla/
  __init__.py
  dependencies.py    — get_sla_repo
  schemas.py         — Request/response Pydantic models
  routers.py         — REST endpoints
```

Router prefix: `/api/v1/sla`

## Celery Periodic Task

```
core/tasks/sla.py
```

### check_sla_breaches (runs every 5 minutes)
1. Get all companies with active SLA policies
2. For each company, get all open requests (status not RESOLVED/REJECTED)
3. For each open request:
   a. Find matching SLA policy (priority + type, fallback priority-only)
   b. If no policy → skip
   c. Calculate response time (created_at → first_response_at or now)
   d. Calculate resolution time (created_at → now)
   e. Check warning thresholds (75% of target by default)
   f. Check breach thresholds (100% of target)
   g. If new breach detected (not already recorded) → save breach record + send notification
   h. If escalate_on_breach → auto-escalate priority

### first_response_at tracking
Add `first_response_at` field to ServiceRequest. Set when status first changes from SUBMITTED to IN_REVIEW (or any later status). This is set in the ChangeRequestStatusCommand handler if not already set.

## Notification Integration

New EventType values:
- `SLA_WARNING` — Warning threshold reached
- `SLA_RESPONSE_BREACHED` — Response time exceeded
- `SLA_RESOLUTION_BREACHED` — Resolution time exceeded

Target resolution:
- `SLA_WARNING` → assigned technician
- `SLA_RESPONSE_BREACHED` → assigned technician + all admins
- `SLA_RESOLUTION_BREACHED` → assigned technician + all admins

## Report Integration

New report type: `sla_compliance` in `core/tasks/report_data.py`

Report data:
- Period (from_date, to_date)
- Total requests resolved in period
- SLA met count / breached count
- Compliance percentage
- Average response time by priority
- Average resolution time by priority
- Top breached requests

## Frontend

### Pages
- `SlaPolicesPage` — List/create/edit SLA policies (admin)
- `SlaDashboardPage` — Compliance metrics dashboard (admin)
- SLA status badge on request detail pages

### Sidebar
- Add under Operations section: "SLA Policies" (admin only)
- Add under Operations section: "SLA Dashboard" (admin only)

## Migration from Hardcoded Thresholds

After E19 is deployed:
- The hardcoded `SLA_THRESHOLDS_HOURS` in constants.py remains as fallback
- Dashboard SLA alerts endpoint uses policy-based data when policies exist, falls back to hardcoded thresholds
- No breaking changes to existing functionality

## Testing Strategy

### Unit Tests
- Domain: SlaPolicy.create validation, breach record creation
- Commands: create/update/deactivate policy handlers
- Queries: SLA status calculation, dashboard metrics

### Integration Tests
- Policy CRUD endpoints
- SLA status endpoint
- Dashboard endpoint
- Plan gate enforcement (only Enterprise)

### Celery Task Tests
- Breach detection logic (mock repositories)
- Warning vs breach threshold detection
- Idempotent breach recording (no duplicates)
