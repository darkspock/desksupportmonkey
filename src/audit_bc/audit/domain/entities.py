import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import ulid

from src.audit_bc.audit.domain.enums import (
    ComplianceStatus,
    EvidenceType,
    GdprRequestStatus,
    GdprRequestType,
)


@dataclass
class ComplianceControl:
    id: str
    company_id: Optional[str]
    code: str
    name: str
    framework: str
    description: Optional[str]
    is_predefined: bool
    is_active: bool
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: Optional[str],
        code: str,
        name: str,
        framework: str,
        description: Optional[str] = None,
        is_predefined: bool = False,
    ) -> "ComplianceControl":
        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            code=code,
            name=name,
            framework=framework,
            description=description,
            is_predefined=is_predefined,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )


@dataclass
class AuditEntryTag:
    id: str
    audit_entry_id: str
    control_id: str
    tagged_by: str
    tagged_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        audit_entry_id: str,
        control_id: str,
        tagged_by: str,
    ) -> "AuditEntryTag":
        return cls(
            id=str(ulid.new()),
            audit_entry_id=audit_entry_id,
            control_id=control_id,
            tagged_by=tagged_by,
            tagged_at=datetime.now(timezone.utc),
        )


@dataclass
class AuditEntry:
    id: str
    company_id: Optional[str]
    actor_id: Optional[str]
    actor_email: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    http_method: str
    http_path: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_data: Optional[dict]
    response_status: int
    changes: Optional[dict]
    hash: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: Optional[str],
        actor_id: Optional[str],
        actor_email: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        http_method: str,
        http_path: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        request_data: Optional[dict],
        response_status: int,
        changes: Optional[dict] = None,
    ) -> "AuditEntry":
        now = datetime.now(timezone.utc)
        hash_value = cls.compute_hash(
            company_id=company_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            created_at=now,
        )
        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            http_method=http_method,
            http_path=http_path,
            ip_address=ip_address,
            user_agent=user_agent,
            request_data=request_data,
            response_status=response_status,
            changes=changes,
            hash=hash_value,
            created_at=now,
        )

    @staticmethod
    def compute_hash(
        company_id: Optional[str],
        actor_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        created_at: datetime,
    ) -> str:
        data = (
            f"{company_id or ''}|{actor_id or ''}|{action}"
            f"|{resource_type}|{resource_id or ''}"
            f"|{created_at.isoformat()}"
        )
        return hashlib.sha256(data.encode()).hexdigest()


VALID_RETENTION_MONTHS = [0, 12, 24, 36, 60, 84]


@dataclass
class RetentionPolicy:
    id: str
    company_id: str
    retention_months: int
    updated_at: Optional[datetime]
    updated_by: str

    @classmethod
    def create(
        cls,
        company_id: str,
        retention_months: int = 36,
        updated_by: str = "",
    ) -> "RetentionPolicy":
        if retention_months not in VALID_RETENTION_MONTHS:
            from src.audit_bc.audit.domain.exceptions import (
                InvalidRetentionPeriodError,
            )
            raise InvalidRetentionPeriodError(
                f"Invalid retention period: {retention_months}"
            )
        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            retention_months=retention_months,
            updated_at=datetime.now(timezone.utc),
            updated_by=updated_by,
        )


@dataclass
class GdprRequest:
    id: str
    company_id: str
    target_user_id: str
    target_user_email: str
    requested_by: str
    request_type: GdprRequestType
    status: GdprRequestStatus
    reason: Optional[str] = None
    storage_key: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        target_user_id: str,
        target_user_email: str,
        requested_by: str,
        request_type: GdprRequestType,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> "GdprRequest":
        return cls(
            id=request_id or str(ulid.new()),
            company_id=company_id,
            target_user_id=target_user_id,
            target_user_email=target_user_email,
            requested_by=requested_by,
            request_type=request_type,
            status=GdprRequestStatus.PENDING,
            reason=reason,
            created_at=datetime.now(timezone.utc),
        )

    def start_processing(self) -> None:
        from src.audit_bc.audit.domain.exceptions import (
            InvalidGdprStatusTransitionError,
        )
        if self.status != GdprRequestStatus.PENDING:
            raise InvalidGdprStatusTransitionError(
                f"Cannot start processing from {self.status.value}"
            )
        self.status = GdprRequestStatus.PROCESSING
        self.started_at = datetime.now(timezone.utc)

    def complete(self, storage_key: Optional[str] = None) -> None:
        from src.audit_bc.audit.domain.exceptions import (
            InvalidGdprStatusTransitionError,
        )
        if self.status != GdprRequestStatus.PROCESSING:
            raise InvalidGdprStatusTransitionError(
                f"Cannot complete from {self.status.value}"
            )
        self.status = GdprRequestStatus.COMPLETED
        self.storage_key = storage_key
        self.completed_at = datetime.now(timezone.utc)

    def fail(self, error_message: str) -> None:
        from src.audit_bc.audit.domain.exceptions import (
            InvalidGdprStatusTransitionError,
        )
        if self.status != GdprRequestStatus.PROCESSING:
            raise InvalidGdprStatusTransitionError(
                f"Cannot fail from {self.status.value}"
            )
        self.status = GdprRequestStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        from src.audit_bc.audit.domain.exceptions import (
            InvalidGdprStatusTransitionError,
        )
        if self.status != GdprRequestStatus.PENDING:
            raise InvalidGdprStatusTransitionError(
                f"Cannot cancel from {self.status.value}"
            )
        self.status = GdprRequestStatus.CANCELLED


@dataclass
class ComplianceAssessment:
    id: str
    company_id: str
    control_id: str
    status: ComplianceStatus
    notes: Optional[str]
    assessed_by: str
    assessed_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def create(
        cls,
        company_id: str,
        control_id: str,
        status: ComplianceStatus,
        assessed_by: str,
        notes: Optional[str] = None,
    ) -> "ComplianceAssessment":
        now = datetime.now(timezone.utc)
        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            control_id=control_id,
            status=status,
            notes=notes,
            assessed_by=assessed_by,
            assessed_at=now,
            created_at=now,
            updated_at=now,
        )

    def update_status(
        self,
        status: ComplianceStatus,
        notes: Optional[str],
        assessed_by: str,
    ) -> None:
        self.status = status
        self.notes = notes
        self.assessed_by = assessed_by
        self.assessed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class ComplianceEvidence:
    id: str
    company_id: str
    control_id: str
    evidence_type: EvidenceType
    reference_id: Optional[str]
    title: str
    description: Optional[str]
    url: Optional[str]
    added_by: str
    created_at: Optional[datetime]

    @classmethod
    def create(
        cls,
        company_id: str,
        control_id: str,
        evidence_type: EvidenceType,
        title: str,
        added_by: str,
        reference_id: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
    ) -> "ComplianceEvidence":
        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            control_id=control_id,
            evidence_type=evidence_type,
            reference_id=reference_id,
            title=title,
            description=description,
            url=url,
            added_by=added_by,
            created_at=datetime.now(timezone.utc),
        )
