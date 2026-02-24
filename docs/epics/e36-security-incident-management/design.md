# Technical Design: E36 — Security Incident Management (NIS2)

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-23
**Bounded Context:** `incident_bc`

---

## 1. Domain Layer

### 1.1 Enums

**File:** `src/incident_bc/incident/domain/enums.py`

```python
from enum import Enum

class IncidentType(str, Enum):
    MALWARE = "malware"
    DATA_BREACH = "data_breach"
    DDOS = "ddos"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PHISHING = "phishing"
    RANSOMWARE = "ransomware"
    OTHER = "other"

class IncidentSeverity(str, Enum):
    P1 = "P1"  # Critical
    P2 = "P2"  # High
    P3 = "P3"  # Medium
    P4 = "P4"  # Low

class IncidentStatus(str, Enum):
    DETECTED = "detected"
    TRIAGED = "triaged"
    CONTAINED = "contained"
    ERADICATED = "eradicated"
    RECOVERED = "recovered"
    CLOSED = "closed"

class TimelineEventType(str, Enum):
    STATUS_CHANGE = "status_change"
    SEVERITY_CHANGE = "severity_change"
    ASSIGNMENT = "assignment"
    COMMENT = "comment"
    ASSET_LINKED = "asset_linked"
    ASSET_UNLINKED = "asset_unlinked"
    VENDOR_LINKED = "vendor_linked"
    VENDOR_UNLINKED = "vendor_unlinked"
    REPORT_GENERATED = "report_generated"
    REPORT_REGENERATED = "report_regenerated"
    REPORT_SUBMITTED = "report_submitted"
    ESCALATION = "escalation"
    POSTMORTEM_CREATED = "postmortem_created"
    POSTMORTEM_UPDATED = "postmortem_updated"
    INCIDENT_CREATED = "incident_created"
    INCIDENT_UPDATED = "incident_updated"

class ReportType(str, Enum):
    EARLY_WARNING_24H = "early_warning_24h"
    DETAILED_72H = "detailed_72h"
    FINAL_30D = "final_30d"

class ReportStatus(str, Enum):
    PENDING = "pending"
    GENERATED = "generated"
    SUBMITTED = "submitted"
```

### 1.2 State Machine

**Valid transitions for SecurityIncident:**

```python
VALID_STATUS_TRANSITIONS: dict[IncidentStatus, list[IncidentStatus]] = {
    IncidentStatus.DETECTED: [IncidentStatus.TRIAGED, IncidentStatus.CLOSED],
    IncidentStatus.TRIAGED: [IncidentStatus.CONTAINED, IncidentStatus.CLOSED],
    IncidentStatus.CONTAINED: [IncidentStatus.ERADICATED, IncidentStatus.CLOSED],
    IncidentStatus.ERADICATED: [IncidentStatus.RECOVERED, IncidentStatus.CLOSED],
    IncidentStatus.RECOVERED: [IncidentStatus.CLOSED],
    IncidentStatus.CLOSED: [],  # Terminal state
}
```

**Rules:**
- Forward transitions follow the linear path: detected → triaged → contained → eradicated → recovered → closed
- Any active state can skip to `closed` (false alarm/duplicate), but requires `close_reason`
- The `recovered → closed` transition does NOT require `close_reason` (normal closure)

### 1.3 Entities

**File:** `src/incident_bc/incident/domain/entities.py`

```python
@dataclass
class SecurityIncident:
    id: str
    company_id: str
    title: str
    description: str
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    attack_vector: Optional[str]
    data_breach_scope: Optional[str]
    reported_by: str
    assigned_to: Optional[str]
    detected_at: datetime
    close_reason: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    closed_at: Optional[datetime]

    @classmethod
    def create(cls, ...) -> "SecurityIncident":
        """Factory method — validates required fields, sets status=DETECTED"""

    def change_status(self, new_status: IncidentStatus, close_reason: Optional[str] = None) -> None:
        """Validates transition, enforces close_reason for early closure"""

    def change_severity(self, new_severity: IncidentSeverity) -> None:
        """Updates severity, validates not closed"""

    def assign_to(self, user_id: str) -> None:
        """Assigns incident to a user, validates not closed"""

    def update_details(self, title: str, description: str, ...) -> None:
        """Updates editable fields, validates not closed"""
```

```python
@dataclass
class IncidentTimeline:
    id: str
    incident_id: str
    event_type: TimelineEventType
    description: str
    actor_id: str
    created_at: Optional[datetime]
    metadata: Optional[dict]

    @classmethod
    def create(cls, incident_id: str, event_type: TimelineEventType,
               description: str, actor_id: str, metadata: Optional[dict] = None) -> "IncidentTimeline":
        """Factory method"""
```

```python
@dataclass
class RegulatoryReport:
    id: str
    incident_id: str
    report_type: ReportType
    status: ReportStatus
    deadline_at: datetime
    generated_at: Optional[datetime]
    submitted_at: Optional[datetime]
    file_path: Optional[str]

    @classmethod
    def create_for_incident(cls, incident_id: str, detected_at: datetime) -> list["RegulatoryReport"]:
        """Factory method — creates 3 reports with calculated deadlines"""
        # 24h = detected_at + timedelta(hours=24)
        # 72h = detected_at + timedelta(hours=72)
        # 30d = detected_at + timedelta(days=30)

    def mark_generated(self, file_path: str) -> None:
        """Transitions pending/generated → generated, updates file_path"""

    def mark_submitted(self) -> None:
        """Transitions generated → submitted"""
```

```python
@dataclass
class PostMortem:
    id: str
    incident_id: str
    root_cause: str
    lessons_learned: str
    corrective_actions: str
    created_by: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def create(cls, incident_id: str, root_cause: str, lessons_learned: str,
               corrective_actions: str, created_by: str) -> "PostMortem":
        """Factory method — validates required fields"""
```

### 1.4 Repository Interface

**File:** `src/incident_bc/incident/domain/repository.py`

```python
class IncidentRepositoryInterface(ABC):
    # SecurityIncident
    @abstractmethod
    def save(self, incident: SecurityIncident) -> None: ...
    @abstractmethod
    def find_by_id(self, incident_id: str, company_id: str) -> Optional[SecurityIncident]: ...
    @abstractmethod
    def find_all(self, company_id: str, filters: IncidentFilters) -> tuple[list[SecurityIncident], int]: ...

    # IncidentTimeline
    @abstractmethod
    def save_timeline(self, entry: IncidentTimeline) -> None: ...
    @abstractmethod
    def find_timeline(self, incident_id: str) -> list[IncidentTimeline]: ...

    # RegulatoryReport
    @abstractmethod
    def save_report(self, report: RegulatoryReport) -> None: ...
    @abstractmethod
    def save_reports_batch(self, reports: list[RegulatoryReport]) -> None: ...
    @abstractmethod
    def find_report_by_id(self, report_id: str, incident_id: str) -> Optional[RegulatoryReport]: ...
    @abstractmethod
    def find_reports_by_incident(self, incident_id: str) -> list[RegulatoryReport]: ...
    @abstractmethod
    def find_pending_reports_approaching_deadline(self) -> list[tuple[RegulatoryReport, SecurityIncident]]: ...

    # IncidentAsset
    @abstractmethod
    def save_incident_asset(self, incident_id: str, asset_id: str, impact_description: Optional[str]) -> str: ...
    @abstractmethod
    def delete_incident_asset(self, incident_id: str, asset_id: str) -> None: ...
    @abstractmethod
    def find_assets_by_incident(self, incident_id: str) -> list[dict]: ...

    # IncidentVendor
    @abstractmethod
    def save_incident_vendor(self, incident_id: str, vendor_id: str, involvement_description: Optional[str]) -> str: ...
    @abstractmethod
    def delete_incident_vendor(self, incident_id: str, vendor_id: str) -> None: ...
    @abstractmethod
    def find_vendors_by_incident(self, incident_id: str) -> list[dict]: ...

    # PostMortem
    @abstractmethod
    def save_postmortem(self, postmortem: PostMortem) -> None: ...
    @abstractmethod
    def find_postmortem_by_incident(self, incident_id: str) -> Optional[PostMortem]: ...

    # Dashboard
    @abstractmethod
    def get_dashboard_stats(self, company_id: str) -> dict: ...
    @abstractmethod
    def find_my_incidents(self, user_id: str, company_id: str) -> list[SecurityIncident]: ...
```

### 1.5 Domain Exceptions

**File:** `src/incident_bc/incident/domain/exceptions.py`

```python
class IncidentNotFoundError(Exception): ...
class InvalidStatusTransitionError(Exception): ...
class CloseReasonRequiredError(Exception): ...
class IncidentClosedError(Exception): ...        # Cannot modify closed incident
class ReportNotFoundError(Exception): ...
class ReportNotGeneratedError(Exception): ...     # Cannot submit ungeneratedreport
class PostMortemAlreadyExistsError(Exception): ...
class PostMortemNotFoundError(Exception): ...
class IncidentNotClosableForPostMortemError(Exception): ...  # Status not recovered/closed
class AssetAlreadyLinkedError(Exception): ...
class AssetNotLinkedError(Exception): ...
class VendorAlreadyLinkedError(Exception): ...
class VendorNotLinkedError(Exception): ...
```

---

## 2. Application Layer

### 2.1 Commands (F0 — Foundation)

| File | Command | Handler Returns |
|------|---------|-----------------|
| `commands/create_incident.py` | `CreateIncidentCommand(id, company_id, title, description, incident_type, severity, detected_at, attack_vector?, data_breach_scope?, reported_by)` | `None` |
| `commands/update_incident.py` | `UpdateIncidentCommand(id, company_id, title?, description?, attack_vector?, data_breach_scope?)` | `None` |
| `commands/change_status.py` | `ChangeIncidentStatusCommand(id, company_id, new_status, close_reason?, actor_id)` | `None` |
| `commands/change_severity.py` | `ChangeIncidentSeverityCommand(id, company_id, new_severity, actor_id)` | `None` |
| `commands/assign_incident.py` | `AssignIncidentCommand(id, company_id, assigned_to, actor_id)` | `None` |

### 2.2 Commands (F1 — Regulatory Reports)

| File | Command | Handler Returns |
|------|---------|-----------------|
| `commands/generate_report.py` | `GenerateReportCommand(incident_id, report_id, company_id, actor_id)` | `None` |
| `commands/submit_report.py` | `SubmitReportCommand(incident_id, report_id, company_id, actor_id)` | `None` |

### 2.3 Commands (F2 — Asset/Vendor Linking)

| File | Command | Handler Returns |
|------|---------|-----------------|
| `commands/link_asset.py` | `LinkAssetCommand(incident_id, company_id, asset_id, impact_description?, actor_id)` | `None` |
| `commands/unlink_asset.py` | `UnlinkAssetCommand(incident_id, company_id, asset_id, actor_id)` | `None` |
| `commands/link_vendor.py` | `LinkVendorCommand(incident_id, company_id, vendor_id, involvement_description?, actor_id)` | `None` |
| `commands/unlink_vendor.py` | `UnlinkVendorCommand(incident_id, company_id, vendor_id, actor_id)` | `None` |

### 2.4 Commands (F3 — Post-Mortem & Employee)

| File | Command | Handler Returns |
|------|---------|-----------------|
| `commands/create_postmortem.py` | `CreatePostMortemCommand(incident_id, company_id, root_cause, lessons_learned, corrective_actions, actor_id)` | `None` |
| `commands/update_postmortem.py` | `UpdatePostMortemCommand(incident_id, company_id, root_cause?, lessons_learned?, corrective_actions?, actor_id)` | `None` |
| `commands/report_incident_employee.py` | `ReportIncidentCommand(company_id, title, description, incident_type, reported_by)` | `None` |

### 2.5 Queries

| File | Query | Returns |
|------|-------|---------|
| `queries/list_incidents.py` | `ListIncidentsQuery(company_id, page, page_size, status?, severity?, type?, search?, date_from?, date_to?)` | `tuple[list[IncidentListDto], int]` |
| `queries/get_incident_detail.py` | `GetIncidentDetailQuery(id, company_id)` | `IncidentDetailDto` |
| `queries/list_reports.py` | `ListReportsQuery(incident_id, company_id)` | `list[ReportDto]` |
| `queries/get_postmortem.py` | `GetPostMortemQuery(incident_id, company_id)` | `Optional[PostMortemDto]` |
| `queries/list_my_incidents.py` | `ListMyIncidentsQuery(user_id, company_id)` | `list[MyIncidentDto]` |
| `queries/get_dashboard.py` | `GetDashboardQuery(company_id)` | `DashboardDto` |

### 2.6 DTOs

```python
@dataclass
class IncidentListDto:
    id: str
    title: str
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    detected_at: datetime
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

@dataclass
class IncidentDetailDto:
    # All fields from IncidentListDto plus:
    description: str
    attack_vector: Optional[str]
    data_breach_scope: Optional[str]
    reported_by: str
    reported_by_name: Optional[str]
    close_reason: Optional[str]
    closed_at: Optional[datetime]
    timeline: list["TimelineEntryDto"]
    reports: list["ReportDto"]          # F1
    assets: list["IncidentAssetDto"]    # F2
    vendors: list["IncidentVendorDto"]  # F2
    postmortem: Optional["PostMortemDto"]  # F3

@dataclass
class TimelineEntryDto:
    id: str
    event_type: TimelineEventType
    description: str
    actor_id: str
    actor_name: Optional[str]
    created_at: datetime
    metadata: Optional[dict]

@dataclass
class ReportDto:
    id: str
    report_type: ReportType
    status: ReportStatus
    deadline_at: datetime
    generated_at: Optional[datetime]
    submitted_at: Optional[datetime]
    time_remaining_seconds: Optional[int]  # Computed: deadline_at - now()
    elapsed_percentage: float              # Computed: elapsed / total * 100

@dataclass
class PostMortemDto:
    id: str
    root_cause: str
    lessons_learned: str
    corrective_actions: str
    created_by: str
    created_by_name: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

@dataclass
class MyIncidentDto:
    """Restricted DTO for employee view — no sensitive fields"""
    id: str
    title: str
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    created_at: Optional[datetime]

@dataclass
class IncidentAssetDto:
    asset_id: str
    asset_name: str
    asset_type: Optional[str]
    impact_description: Optional[str]

@dataclass
class IncidentVendorDto:
    vendor_id: str
    vendor_name: str
    involvement_description: Optional[str]

@dataclass
class DashboardDto:
    total_active: int
    total_closed: int
    active_by_severity: dict[str, int]   # {"P1": 2, "P2": 5, ...}
    by_type: dict[str, int]              # {"malware": 3, "phishing": 7, ...}
    mttc_hours: Optional[float]          # Mean Time to Contain
    mttr_hours: Optional[float]          # Mean Time to Resolve
    upcoming_deadlines: list["UpcomingDeadlineDto"]
    recent_incidents: list[IncidentListDto]

@dataclass
class UpcomingDeadlineDto:
    incident_id: str
    incident_title: str
    report_type: ReportType
    deadline_at: datetime
    time_remaining_seconds: int
```

### 2.7 Event Factory

**File:** `src/incident_bc/incident/application/services/incident_event_factory.py`

```python
class IncidentEventFactory:
    @staticmethod
    def incident_created(incident: SecurityIncident, actor_id: str) -> DomainEvent: ...
    @staticmethod
    def status_changed(incident: SecurityIncident, old_status: str, new_status: str, actor_id: str) -> DomainEvent: ...
    @staticmethod
    def severity_changed(incident: SecurityIncident, old_severity: str, new_severity: str, actor_id: str) -> DomainEvent: ...
    @staticmethod
    def incident_assigned(incident: SecurityIncident, assigned_to: str, actor_id: str) -> DomainEvent: ...
    @staticmethod
    def deadline_warning(incident: SecurityIncident, report_type: str, percentage: int) -> DomainEvent: ...
    @staticmethod
    def deadline_passed(incident: SecurityIncident, report_type: str) -> DomainEvent: ...
```

**New EventType values** (add to `src/notification_bc/notification/domain/enums.py`):

```python
INCIDENT_CREATED = "incident.created"
INCIDENT_STATUS_CHANGED = "incident.status_changed"
INCIDENT_SEVERITY_CHANGED = "incident.severity_changed"
INCIDENT_ASSIGNED = "incident.assigned"
INCIDENT_DEADLINE_WARNING = "incident.deadline_warning"
INCIDENT_DEADLINE_URGENT = "incident.deadline_urgent"
INCIDENT_DEADLINE_PASSED = "incident.deadline_passed"
INCIDENT_EMPLOYEE_REPORTED = "incident.employee_reported"
```

**Target resolution** (add to `target_resolver.py`):
- `INCIDENT_CREATED` → all admins
- `INCIDENT_STATUS_CHANGED` → assigned user + all admins
- `INCIDENT_SEVERITY_CHANGED` → assigned user + all admins
- `INCIDENT_ASSIGNED` → assigned user
- `INCIDENT_DEADLINE_WARNING` → assigned user + all admins
- `INCIDENT_DEADLINE_URGENT` → all admins
- `INCIDENT_DEADLINE_PASSED` → all admins
- `INCIDENT_EMPLOYEE_REPORTED` → all admins + all technicians

---

## 3. Infrastructure Layer

### 3.1 ORM Models

**File:** `src/incident_bc/incident/infrastructure/models.py`

```python
class SecurityIncidentModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "security_incidents"

    company_id: Mapped[str] = mapped_column(String(26), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    incident_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(5), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="detected")
    attack_vector: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    data_breach_scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reported_by: Mapped[str] = mapped_column(String(26), nullable=False)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    close_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Indexes
    __table_args__ = (
        Index("ix_security_incidents_company_status", "company_id", "status"),
        Index("ix_security_incidents_company_severity", "company_id", "severity"),
        Index("ix_security_incidents_company_type", "company_id", "incident_type"),
        Index("ix_security_incidents_detected_at", "detected_at"),
    )

class IncidentTimelineModel(ULIDMixin, Base):
    __tablename__ = "incident_timeline"

    incident_id: Mapped[str] = mapped_column(String(26), ForeignKey("security_incidents.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(26), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

class IncidentAssetModel(ULIDMixin, Base):
    __tablename__ = "incident_assets"

    incident_id: Mapped[str] = mapped_column(String(26), ForeignKey("security_incidents.id"), nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(String(26), nullable=False)
    impact_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("incident_id", "asset_id", name="uq_incident_asset"),
    )

class IncidentVendorModel(ULIDMixin, Base):
    __tablename__ = "incident_vendors"

    incident_id: Mapped[str] = mapped_column(String(26), ForeignKey("security_incidents.id"), nullable=False, index=True)
    vendor_id: Mapped[str] = mapped_column(String(26), nullable=False)
    involvement_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("incident_id", "vendor_id", name="uq_incident_vendor"),
    )

class RegulatoryReportModel(ULIDMixin, Base):
    __tablename__ = "regulatory_reports"

    incident_id: Mapped[str] = mapped_column(String(26), ForeignKey("security_incidents.id"), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(15), nullable=False, server_default="pending")
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        Index("ix_regulatory_reports_deadline", "deadline_at"),
        Index("ix_regulatory_reports_status", "status"),
    )

class PostMortemModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "post_mortems"

    incident_id: Mapped[str] = mapped_column(String(26), ForeignKey("security_incidents.id"), nullable=False, unique=True)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    lessons_learned: Mapped[str] = mapped_column(Text, nullable=False)
    corrective_actions: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(26), nullable=False)
```

### 3.2 Database Migration

**File:** `alembic/versions/xxx_create_incident_tables.py`

Creates all 6 tables in a single migration:
1. `security_incidents` — with composite indexes on (company_id, status), (company_id, severity), (company_id, incident_type)
2. `incident_timeline` — FK to security_incidents, indexed on incident_id
3. `incident_assets` — FK to security_incidents, unique constraint on (incident_id, asset_id)
4. `incident_vendors` — FK to security_incidents, unique constraint on (incident_id, vendor_id)
5. `regulatory_reports` — FK to security_incidents, indexed on deadline_at and status
6. `post_mortems` — FK to security_incidents, unique on incident_id (one-to-one)

---

## 4. HTTP Layer

### 4.1 Router Organization

**Directory:** `adapters/http/api/incidents/`

```
incidents/
├── __init__.py
├── routers.py        # All incident endpoints
├── schemas.py        # Pydantic request/response models
└── dependencies.py   # Repository injection
```

### 4.2 Schemas

**File:** `adapters/http/api/incidents/schemas.py`

```python
# --- Requests ---
class CreateIncidentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    incident_type: str  # Validated against IncidentType enum
    severity: str       # Validated against IncidentSeverity enum
    detected_at: datetime
    attack_vector: Optional[str] = Field(None, max_length=500)
    data_breach_scope: Optional[str] = None

class UpdateIncidentRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    attack_vector: Optional[str] = Field(None, max_length=500)
    data_breach_scope: Optional[str] = None

class ChangeStatusRequest(BaseModel):
    status: str
    close_reason: Optional[str] = None

class ChangeSeverityRequest(BaseModel):
    severity: str

class AssignRequest(BaseModel):
    assigned_to: str

class LinkAssetRequest(BaseModel):
    asset_id: str
    impact_description: Optional[str] = None

class LinkVendorRequest(BaseModel):
    vendor_id: str
    involvement_description: Optional[str] = None

class CreatePostMortemRequest(BaseModel):
    root_cause: str = Field(min_length=1)
    lessons_learned: str = Field(min_length=1)
    corrective_actions: str = Field(min_length=1)

class UpdatePostMortemRequest(BaseModel):
    root_cause: Optional[str] = Field(None, min_length=1)
    lessons_learned: Optional[str] = Field(None, min_length=1)
    corrective_actions: Optional[str] = Field(None, min_length=1)

class ReportIncidentRequest(BaseModel):
    """Simplified form for employees"""
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    incident_type: str

# --- Responses ---
class IncidentListResponse(BaseModel):
    id: str
    title: str
    incident_type: str
    severity: str
    status: str
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    detected_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class IncidentDetailResponse(BaseModel):
    id: str
    title: str
    description: str
    incident_type: str
    severity: str
    status: str
    attack_vector: Optional[str] = None
    data_breach_scope: Optional[str] = None
    reported_by: str
    reported_by_name: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    detected_at: Optional[datetime] = None
    close_reason: Optional[str] = None
    closed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    timeline: list["TimelineEntryResponse"] = []
    reports: list["ReportResponse"] = []
    assets: list["IncidentAssetResponse"] = []
    vendors: list["IncidentVendorResponse"] = []
    postmortem: Optional["PostMortemResponse"] = None

class TimelineEntryResponse(BaseModel):
    id: str
    event_type: str
    description: str
    actor_name: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[dict] = None

class ReportResponse(BaseModel):
    id: str
    report_type: str
    status: str
    deadline_at: Optional[datetime] = None
    generated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    time_remaining_seconds: Optional[int] = None
    elapsed_percentage: Optional[float] = None

class PostMortemResponse(BaseModel):
    id: str
    root_cause: str
    lessons_learned: str
    corrective_actions: str
    created_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class IncidentAssetResponse(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: Optional[str] = None
    impact_description: Optional[str] = None

class IncidentVendorResponse(BaseModel):
    vendor_id: str
    vendor_name: str
    involvement_description: Optional[str] = None

class DashboardResponse(BaseModel):
    total_active: int
    total_closed: int
    active_by_severity: dict
    by_type: dict
    mttc_hours: Optional[float] = None
    mttr_hours: Optional[float] = None
    upcoming_deadlines: list = []
    recent_incidents: list = []

class MyIncidentResponse(BaseModel):
    id: str
    title: str
    incident_type: str
    severity: str
    status: str
    created_at: Optional[datetime] = None
```

### 4.3 Endpoint Summary

| Method | Path | Role | Feature |
|--------|------|------|---------|
| POST | `/api/v1/incidents` | technician, admin | F0 |
| GET | `/api/v1/incidents` | technician, admin | F0 |
| GET | `/api/v1/incidents/{id}` | technician, admin | F0 |
| PUT | `/api/v1/incidents/{id}` | technician, admin | F0 |
| POST | `/api/v1/incidents/{id}/status` | technician, admin | F0 |
| POST | `/api/v1/incidents/{id}/severity` | technician, admin | F0 |
| POST | `/api/v1/incidents/{id}/assign` | admin | F0 |
| GET | `/api/v1/incidents/{id}/reports` | technician, admin | F1 |
| POST | `/api/v1/incidents/{id}/reports/{report_id}/generate` | admin | F1 |
| POST | `/api/v1/incidents/{id}/reports/{report_id}/submit` | admin | F1 |
| GET | `/api/v1/incidents/{id}/reports/{report_id}/download` | admin | F1 |
| POST | `/api/v1/incidents/{id}/assets` | technician, admin | F2 |
| DELETE | `/api/v1/incidents/{id}/assets/{asset_id}` | technician, admin | F2 |
| POST | `/api/v1/incidents/{id}/vendors` | technician, admin | F2 |
| DELETE | `/api/v1/incidents/{id}/vendors/{vendor_id}` | technician, admin | F2 |
| POST | `/api/v1/incidents/{id}/post-mortem` | admin | F3 |
| GET | `/api/v1/incidents/{id}/post-mortem` | technician, admin | F3 |
| PUT | `/api/v1/incidents/{id}/post-mortem` | admin | F3 |
| GET | `/api/v1/incidents/dashboard` | technician, admin | F4 |
| POST | `/api/v1/my/report-incident` | employee, technician, admin | F3 |
| GET | `/api/v1/my/incidents` | employee, technician, admin | F3 |

### 4.4 Error Handling

| Exception | HTTP Status | Endpoint |
|-----------|-------------|----------|
| `IncidentNotFoundError` | 404 | All incident endpoints |
| `InvalidStatusTransitionError` | 422 | POST .../status |
| `CloseReasonRequiredError` | 422 | POST .../status |
| `IncidentClosedError` | 422 | PUT, POST status/severity/assign, link/unlink |
| `ReportNotFoundError` | 404 | POST .../generate, .../submit, GET .../download |
| `ReportNotGeneratedError` | 422 | POST .../submit, GET .../download |
| `PostMortemAlreadyExistsError` | 409 | POST .../post-mortem |
| `PostMortemNotFoundError` | 404 | GET/PUT .../post-mortem |
| `IncidentNotClosableForPostMortemError` | 422 | POST .../post-mortem |
| `AssetAlreadyLinkedError` | 409 | POST .../assets |
| `AssetNotLinkedError` | 404 | DELETE .../assets/{id} |
| `VendorAlreadyLinkedError` | 409 | POST .../vendors |
| `VendorNotLinkedError` | 404 | DELETE .../vendors/{id} |

---

## 5. Celery Tasks

### 5.1 Deadline Monitoring (F1)

**File:** `core/tasks/incidents.py`

```python
@celery_app.task(name="core.tasks.incidents.check_regulatory_deadlines")
def check_regulatory_deadlines():
    """
    Runs every 15 minutes via Celery beat.
    Checks all pending/generated regulatory reports for approaching deadlines.
    Sends notifications at 75%, 90%, and 100% (overdue) thresholds.
    """
```

**Beat schedule entry** (add to `core/celery.py`):

```python
"check-regulatory-deadlines": {
    "task": "core.tasks.incidents.check_regulatory_deadlines",
    "schedule": crontab(minute="*/15"),
},
```

### 5.2 PDF Generation (F1)

**File:** `core/tasks/incidents.py`

```python
@celery_app.task(
    name="core.tasks.incidents.generate_incident_report",
    bind=True,
    max_retries=3,
)
def generate_incident_report(self, report_id: str, incident_id: str):
    """
    Generates a regulatory report PDF using WeasyPrint.
    1. Load incident + report from DB
    2. Collect data (timeline, assets, vendors)
    3. Render Jinja2 template
    4. Convert to PDF via WeasyPrint
    5. Upload to S3
    6. Update report with file_path + generated_at
    """
```

---

## 6. Frontend Architecture

### 6.1 Pages

| Page | Path | Role | Feature |
|------|------|------|---------|
| Incidents List | `/incidents` | technician, admin | F0 |
| Incident Detail | `/incidents/:id` | technician, admin | F0+ |
| Incident Dashboard | `/incidents/dashboard` | technician, admin | F4 |
| Report Incident (Employee) | `/my/report-incident` | all roles | F3 |
| My Incidents | `/my/incidents` | all roles | F3 |

### 6.2 Components (F0)

- `IncidentsList` — paginated table with status/severity/type filters
- `IncidentDetail` — full detail view with tabs/sections
- `CreateIncidentForm` — modal with mandatory fields
- `IncidentTimeline` — chronological event list
- `IncidentStatusBadge` — color-coded status chip
- `IncidentSeverityBadge` — color-coded P1/P2/P3/P4 chip

### 6.3 Components (F1)

- `RegulatoryReportsSection` — deadline cards with countdown timers
- `CountdownTimer` — live countdown (hours:minutes:seconds remaining)

### 6.4 Components (F2)

- `AffectedAssetsSection` — linked assets list with add/remove
- `InvolvedVendorsSection` — linked vendors list with add/remove

### 6.5 Components (F3)

- `PostMortemSection` — read/create/edit post-mortem
- `ReportIncidentForm` — simplified employee form

### 6.6 Components (F4)

- `IncidentDashboard` — stat cards + charts + deadlines + recent

### 6.7 Sidebar Navigation

Add new "Security" section to sidebar:

```typescript
{
  labelKey: 'nav.security',
  icon: ShieldAlert,  // from lucide-react
  roles: ['admin', 'technician'],
  entries: [
    { labelKey: 'nav.incidents', path: '/incidents', icon: AlertTriangle },
    { labelKey: 'nav.incident_dashboard', path: '/incidents/dashboard', icon: BarChart3 },
  ],
}
```

For employees, add "Report Incident" under My Activity section:
```typescript
{ labelKey: 'nav.report_incident', path: '/my/report-incident', icon: ShieldAlert }
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Location:** `tests/unit/incident_bc/`

| Test File | What It Tests |
|-----------|---------------|
| `test_security_incident.py` | Entity creation, state machine transitions, close_reason validation |
| `test_regulatory_report.py` | Report creation, deadline calculation, state machine |
| `test_postmortem.py` | Post-mortem creation, validation |
| `test_create_incident.py` | CreateIncidentCommandHandler |
| `test_change_status.py` | ChangeStatusCommandHandler |
| `test_change_severity.py` | ChangeSeverityCommandHandler |
| `test_assign_incident.py` | AssignIncidentCommandHandler |
| `test_generate_report.py` | GenerateReportCommandHandler |
| `test_submit_report.py` | SubmitReportCommandHandler |
| `test_link_asset.py` | LinkAssetCommandHandler |
| `test_link_vendor.py` | LinkVendorCommandHandler |
| `test_create_postmortem.py` | CreatePostMortemCommandHandler |
| `test_report_incident_employee.py` | ReportIncidentCommandHandler |
| `test_list_incidents.py` | ListIncidentsQueryHandler |
| `test_get_incident_detail.py` | GetIncidentDetailQueryHandler |
| `test_get_dashboard.py` | GetDashboardQueryHandler |
| `test_check_deadlines.py` | Celery deadline monitoring task |

### 7.2 Integration Tests

**Location:** `tests/integration/`

**File:** `test_incidents_endpoints.py`

Coverage:
- Create incident → verify 201, verify timeline entry, verify notifications
- List incidents → verify pagination, filters (status, severity, type, date range)
- Get incident detail → verify all fields, timeline, reports, assets, vendors, postmortem
- Update incident → verify fields updated, timeline entry
- Change status → all valid transitions + invalid transitions (422)
- Close with reason → verify close_reason mandatory
- Close without reason from recovered → verify allowed
- Change severity → verify updated + timeline
- Assign → verify assigned + timeline + notification
- Link/unlink assets → verify link/unlink + timeline entries
- Link/unlink vendors → verify link/unlink + timeline entries
- Generate report → verify Celery task triggered
- Submit report → verify status change + timeline
- Create post-mortem → verify precondition (recovered/closed)
- Employee report → verify simplified creation + default severity
- Employee my incidents → verify restricted fields
- Dashboard → verify aggregation data
- Role authorization → verify 403 for unauthorized roles

---

## 8. Implementation Order

### Phase 1: F0 — Incident Foundation
1. Create `src/incident_bc/` directory structure
2. Domain layer: enums, entities, exceptions, repository interface
3. Infrastructure layer: ORM models, repository implementation
4. Alembic migration (ALL 6 tables)
5. Application layer: create, update, change_status, change_severity, assign commands
6. Application layer: list_incidents, get_incident_detail queries
7. IncidentEventFactory + notification EventType additions
8. HTTP layer: routers, schemas, dependencies
9. Unit tests for all handlers
10. Integration tests for all endpoints
11. Frontend: sidebar nav, incidents list page, incident detail page, create form
12. i18n: EN/ES translations

### Phase 2: F1 — NIS2 Regulatory Reports
1. Domain: RegulatoryReport entity with state machine
2. Modify CreateIncidentCommandHandler to auto-create 3 reports
3. Commands: generate_report, submit_report
4. Queries: list_reports (enrich incident detail)
5. Celery tasks: generate_incident_report, check_regulatory_deadlines
6. Beat schedule entry
7. PDF template (Jinja2 + WeasyPrint)
8. HTTP endpoints for reports
9. Escalation notification events
10. Unit + integration tests
11. Frontend: regulatory section, countdown timers
12. i18n

### Phase 3: F2 — Asset & Vendor Linking
1. Commands: link_asset, unlink_asset, link_vendor, unlink_vendor
2. Cross-BC port interfaces + implementations
3. Enrich incident detail response with assets/vendors
4. HTTP endpoints
5. Unit + integration tests
6. Frontend: asset/vendor sections
7. i18n

### Phase 4: F3 — Post-Mortem & Employee Reporting
1. Domain: PostMortem entity
2. Commands: create_postmortem, update_postmortem, report_incident (employee)
3. Queries: get_postmortem, list_my_incidents
4. HTTP endpoints (incidents + my)
5. Unit + integration tests
6. Frontend: post-mortem section, employee form, my incidents
7. i18n

### Phase 5: F4 — Incident Dashboard
1. Query: get_dashboard with SQL aggregations
2. HTTP endpoint
3. Unit + integration tests
4. Frontend: dashboard page
5. i18n

---

## 9. Collateral Changes

| File/Component | Change | Feature |
|----------------|--------|---------|
| `src/notification_bc/notification/domain/enums.py` | Add 8 new EventType values | F0, F1 |
| `src/notification_bc/notification/application/services/target_resolver.py` | Add routing rules for incident events | F0, F1 |
| `adapters/http/api/dependencies.py` | Register incident-related subscribers | F0 |
| `adapters/http/main.py` | Include incidents router | F0 |
| `core/celery.py` | Add beat schedule entry for deadline monitoring | F1 |
| `web/app/src/components/layout/Sidebar.tsx` | Add "Security" section | F0 |
| `web/app/src/locales/en.ts` | Add all EN translations | F0-F4 |
| `web/app/src/locales/es.ts` | Add all ES translations | F0-F4 |
| `web/app/src/lib/navigation.ts` | Add incidents routes for role defaults | F0 |
| `adapters/http/api/my/routers.py` | Add employee reporting endpoints | F3 |

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Large F0 scope may delay delivery | F0 can be split into backend-first + frontend sub-phases |
| WeasyPrint system dependency issues | Test PDF generation in staging before F1 production deploy |
| Celery beat deadline monitoring may miss edge cases | Comprehensive unit tests for deadline calculation logic |
| Cross-BC queries (F2) may have performance issues | Use indexed asset_id/vendor_id lookups, not full table scans |
| Regulatory deadlines are time-critical | Use timezone-aware datetimes everywhere, test DST transitions |
