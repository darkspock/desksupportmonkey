from abc import ABC, abstractmethod
from typing import Optional

from datetime import datetime

from src.audit_bc.audit.domain.entities import (
    AuditEntry,
    AuditEntryTag,
    ComplianceAssessment,
    ComplianceControl,
    ComplianceEvidence,
    GdprRequest,
    RetentionPolicy,
)


class AuditRepositoryInterface(ABC):
    @abstractmethod
    def save(self, entry: AuditEntry) -> None: ...

    @abstractmethod
    def find_by_id(
        self, entry_id: str, company_id: Optional[str] = None
    ) -> Optional[AuditEntry]: ...

    # Audit entry queries
    @abstractmethod
    def find_all(
        self, company_id: str, filters: dict
    ) -> tuple[list[AuditEntry], int]: ...

    @abstractmethod
    def find_all_cross_company(
        self, filters: dict
    ) -> tuple[list[AuditEntry], int]: ...

    # Compliance controls
    @abstractmethod
    def save_control(self, control: ComplianceControl) -> None: ...

    @abstractmethod
    def find_control_by_id(
        self, control_id: str, company_id: Optional[str] = None
    ) -> Optional[ComplianceControl]: ...

    @abstractmethod
    def find_controls(self, company_id: str) -> list[ComplianceControl]: ...

    @abstractmethod
    def find_control_by_code(
        self, code: str, company_id: Optional[str] = None
    ) -> Optional[ComplianceControl]: ...

    # Tags
    @abstractmethod
    def save_tag(self, tag: AuditEntryTag) -> None: ...

    @abstractmethod
    def delete_tag(self, tag_id: str) -> None: ...

    @abstractmethod
    def find_tags_by_entry(self, entry_id: str) -> list[AuditEntryTag]: ...

    # GDPR requests
    @abstractmethod
    def save_gdpr_request(self, request: GdprRequest) -> None: ...

    @abstractmethod
    def find_gdpr_request_by_id(
        self, request_id: str, company_id: Optional[str] = None
    ) -> Optional[GdprRequest]: ...

    @abstractmethod
    def find_gdpr_requests(
        self, company_id: str, filters: dict
    ) -> tuple[list[GdprRequest], int]: ...

    @abstractmethod
    def anonymize_actor_email(
        self, actor_id: str, anonymized_email: str
    ) -> int: ...

    # Retention policies
    @abstractmethod
    def save_retention_policy(
        self, policy: RetentionPolicy
    ) -> None: ...

    @abstractmethod
    def find_retention_policy(
        self, company_id: str
    ) -> Optional[RetentionPolicy]: ...

    @abstractmethod
    def find_all_retention_policies(
        self,
    ) -> list[RetentionPolicy]: ...

    @abstractmethod
    def delete_entries_before(
        self, company_id: str, before: datetime
    ) -> int: ...

    # Integrity verification
    @abstractmethod
    def find_entries_for_verification(
        self,
        company_id: str,
        date_from: datetime,
        date_to: datetime,
        page: int,
        page_size: int,
    ) -> list[AuditEntry]: ...

    # Compliance assessments
    @abstractmethod
    def save_assessment(
        self, assessment: ComplianceAssessment
    ) -> None: ...

    @abstractmethod
    def find_assessment(
        self, company_id: str, control_id: str
    ) -> Optional[ComplianceAssessment]: ...

    @abstractmethod
    def find_assessments_by_company(
        self, company_id: str
    ) -> list[ComplianceAssessment]: ...

    @abstractmethod
    def count_assessments_by_status(
        self, company_id: str, framework: Optional[str] = None
    ) -> dict[str, int]: ...

    # Compliance evidence
    @abstractmethod
    def save_evidence(self, evidence: ComplianceEvidence) -> None: ...

    @abstractmethod
    def find_evidence_by_id(
        self, evidence_id: str, company_id: str
    ) -> Optional[ComplianceEvidence]: ...

    @abstractmethod
    def find_evidence_by_control(
        self, control_id: str, company_id: str
    ) -> list[ComplianceEvidence]: ...

    @abstractmethod
    def count_evidence_by_control(
        self, company_id: str
    ) -> dict[str, int]: ...

    @abstractmethod
    def delete_evidence(self, evidence_id: str) -> None: ...
