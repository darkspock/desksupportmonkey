from datetime import datetime
from typing import Optional

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from src.audit_bc.audit.domain.entities import (
    AuditEntry,
    AuditEntryTag,
    ComplianceAssessment,
    ComplianceControl,
    ComplianceEvidence,
    GdprRequest,
    RetentionPolicy,
)
from src.audit_bc.audit.domain.enums import (
    ComplianceStatus,
    EvidenceType,
    GdprRequestStatus,
    GdprRequestType,
)
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.audit_bc.audit.infrastructure.models import (
    AuditEntryModel,
    AuditEntryTagModel,
    ComplianceAssessmentModel,
    ComplianceControlModel,
    ComplianceEvidenceModel,
    GdprRequestModel,
    RetentionPolicyModel,
)


class AuditRepository(AuditRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------
    # AuditEntry
    # ------------------------------------------------------------------

    def save(self, entry: AuditEntry) -> None:
        model = AuditEntryModel(
            id=entry.id,
            company_id=entry.company_id,
            actor_id=entry.actor_id,
            actor_email=entry.actor_email,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            http_method=entry.http_method,
            http_path=entry.http_path,
            ip_address=entry.ip_address,
            user_agent=entry.user_agent,
            request_data=entry.request_data,
            response_status=entry.response_status,
            changes=entry.changes,
            hash=entry.hash,
            created_at=entry.created_at,
        )
        self.session.add(model)
        self.session.flush()

    def find_by_id(
        self, entry_id: str, company_id: Optional[str] = None
    ) -> Optional[AuditEntry]:
        stmt = select(AuditEntryModel).where(AuditEntryModel.id == entry_id)
        if company_id is not None:
            stmt = stmt.where(AuditEntryModel.company_id == company_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    def find_all(
        self, company_id: str, filters: dict
    ) -> tuple[list[AuditEntry], int]:
        query = select(AuditEntryModel).where(
            AuditEntryModel.company_id == company_id
        )
        query = self._apply_filters(query, filters)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.session.execute(count_query).scalar() or 0

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        offset = (page - 1) * page_size
        query = query.order_by(AuditEntryModel.created_at.desc())
        query = query.offset(offset).limit(page_size)

        models = self.session.execute(query).scalars().all()
        return [self._to_entity(m) for m in models], total

    def find_all_cross_company(
        self, filters: dict
    ) -> tuple[list[AuditEntry], int]:
        query = select(AuditEntryModel)

        if filters.get("company_id"):
            query = query.where(
                AuditEntryModel.company_id == filters["company_id"]
            )

        query = self._apply_filters(query, filters)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.session.execute(count_query).scalar() or 0

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        offset = (page - 1) * page_size
        query = query.order_by(AuditEntryModel.created_at.desc())
        query = query.offset(offset).limit(page_size)

        models = self.session.execute(query).scalars().all()
        return [self._to_entity(m) for m in models], total

    def _apply_filters(self, query, filters: dict):
        if filters.get("date_from"):
            query = query.where(
                AuditEntryModel.created_at >= filters["date_from"]
            )
        if filters.get("date_to"):
            query = query.where(
                AuditEntryModel.created_at <= filters["date_to"]
            )
        if filters.get("actor_id"):
            query = query.where(
                AuditEntryModel.actor_id == filters["actor_id"]
            )
        if filters.get("action"):
            query = query.where(
                AuditEntryModel.action == filters["action"]
            )
        if filters.get("resource_type"):
            query = query.where(
                AuditEntryModel.resource_type == filters["resource_type"]
            )
        if filters.get("search"):
            term = f"%{filters['search']}%"
            query = query.where(
                or_(
                    AuditEntryModel.resource_id.ilike(term),
                    AuditEntryModel.actor_email.ilike(term),
                )
            )
        if filters.get("control_id"):
            tag_subq = (
                select(AuditEntryTagModel.audit_entry_id)
                .where(AuditEntryTagModel.control_id == filters["control_id"])
                .subquery()
            )
            query = query.where(AuditEntryModel.id.in_(select(tag_subq)))
        return query

    # ------------------------------------------------------------------
    # ComplianceControl
    # ------------------------------------------------------------------

    def save_control(self, control: ComplianceControl) -> None:
        existing = self.session.get(ComplianceControlModel, control.id)
        if existing:
            existing.code = control.code
            existing.name = control.name
            existing.framework = control.framework
            existing.description = control.description
            existing.is_active = control.is_active
        else:
            model = ComplianceControlModel(
                id=control.id,
                company_id=control.company_id,
                code=control.code,
                name=control.name,
                framework=control.framework,
                description=control.description,
                is_predefined=control.is_predefined,
                is_active=control.is_active,
                created_at=control.created_at,
            )
            self.session.add(model)
        self.session.flush()

    def find_control_by_id(
        self, control_id: str, company_id: Optional[str] = None
    ) -> Optional[ComplianceControl]:
        stmt = select(ComplianceControlModel).where(
            ComplianceControlModel.id == control_id
        )
        if company_id is not None:
            stmt = stmt.where(
                or_(
                    ComplianceControlModel.company_id == company_id,
                    ComplianceControlModel.is_predefined.is_(True),
                )
            )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._to_control_entity(model)

    def find_controls(self, company_id: str) -> list[ComplianceControl]:
        stmt = (
            select(ComplianceControlModel)
            .where(
                or_(
                    ComplianceControlModel.company_id == company_id,
                    ComplianceControlModel.company_id.is_(None),
                )
            )
            .where(ComplianceControlModel.is_active.is_(True))
            .order_by(
                ComplianceControlModel.is_predefined.desc(),
                ComplianceControlModel.framework,
                ComplianceControlModel.code,
            )
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._to_control_entity(m) for m in models]

    def find_control_by_code(
        self, code: str, company_id: Optional[str] = None
    ) -> Optional[ComplianceControl]:
        stmt = select(ComplianceControlModel).where(
            ComplianceControlModel.code == code
        )
        if company_id is not None:
            stmt = stmt.where(
                or_(
                    ComplianceControlModel.company_id == company_id,
                    ComplianceControlModel.company_id.is_(None),
                )
            )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._to_control_entity(model)

    # ------------------------------------------------------------------
    # AuditEntryTag
    # ------------------------------------------------------------------

    def save_tag(self, tag: AuditEntryTag) -> None:
        model = AuditEntryTagModel(
            id=tag.id,
            audit_entry_id=tag.audit_entry_id,
            control_id=tag.control_id,
            tagged_by=tag.tagged_by,
            tagged_at=tag.tagged_at,
        )
        self.session.add(model)
        self.session.flush()

    def delete_tag(self, tag_id: str) -> None:
        self.session.execute(
            delete(AuditEntryTagModel).where(AuditEntryTagModel.id == tag_id)
        )
        self.session.flush()

    def find_tags_by_entry(self, entry_id: str) -> list[AuditEntryTag]:
        stmt = (
            select(AuditEntryTagModel)
            .where(AuditEntryTagModel.audit_entry_id == entry_id)
            .order_by(AuditEntryTagModel.tagged_at)
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._to_tag_entity(m) for m in models]

    # ------------------------------------------------------------------
    # Converters
    # ------------------------------------------------------------------

    def _to_entity(self, model: AuditEntryModel) -> AuditEntry:
        return AuditEntry(
            id=model.id,
            company_id=model.company_id,
            actor_id=model.actor_id,
            actor_email=model.actor_email,
            action=model.action,
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            http_method=model.http_method,
            http_path=model.http_path,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            request_data=model.request_data,
            response_status=model.response_status,
            changes=model.changes,
            hash=model.hash,
            created_at=model.created_at,
        )

    def _to_control_entity(
        self, model: ComplianceControlModel
    ) -> ComplianceControl:
        return ComplianceControl(
            id=model.id,
            company_id=model.company_id,
            code=model.code,
            name=model.name,
            framework=model.framework,
            description=model.description,
            is_predefined=model.is_predefined,
            is_active=model.is_active,
            created_at=model.created_at,
        )

    def _to_tag_entity(self, model: AuditEntryTagModel) -> AuditEntryTag:
        return AuditEntryTag(
            id=model.id,
            audit_entry_id=model.audit_entry_id,
            control_id=model.control_id,
            tagged_by=model.tagged_by,
            tagged_at=model.tagged_at,
        )

    # ------------------------------------------------------------------
    # GdprRequest
    # ------------------------------------------------------------------

    def save_gdpr_request(self, request: GdprRequest) -> None:
        existing = self.session.get(GdprRequestModel, request.id)
        if existing:
            existing.status = request.status.value
            existing.reason = request.reason
            existing.storage_key = request.storage_key
            existing.error_message = request.error_message
            existing.started_at = request.started_at
            existing.completed_at = request.completed_at
        else:
            model = GdprRequestModel(
                id=request.id,
                company_id=request.company_id,
                target_user_id=request.target_user_id,
                target_user_email=request.target_user_email,
                requested_by=request.requested_by,
                request_type=request.request_type.value,
                status=request.status.value,
                reason=request.reason,
                storage_key=request.storage_key,
                error_message=request.error_message,
                started_at=request.started_at,
                completed_at=request.completed_at,
                created_at=request.created_at,
            )
            self.session.add(model)
        self.session.flush()

    def find_gdpr_request_by_id(
        self, request_id: str, company_id: Optional[str] = None
    ) -> Optional[GdprRequest]:
        stmt = select(GdprRequestModel).where(
            GdprRequestModel.id == request_id
        )
        if company_id is not None:
            stmt = stmt.where(GdprRequestModel.company_id == company_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._to_gdpr_request_entity(model)

    def find_gdpr_requests(
        self, company_id: str, filters: dict
    ) -> tuple[list[GdprRequest], int]:
        query = select(GdprRequestModel).where(
            GdprRequestModel.company_id == company_id
        )
        if filters.get("status"):
            query = query.where(
                GdprRequestModel.status == filters["status"]
            )
        if filters.get("request_type"):
            query = query.where(
                GdprRequestModel.request_type == filters["request_type"]
            )
        if filters.get("search"):
            term = f"%{filters['search']}%"
            query = query.where(
                GdprRequestModel.target_user_email.ilike(term)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = self.session.execute(count_query).scalar() or 0

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        offset = (page - 1) * page_size
        query = query.order_by(GdprRequestModel.created_at.desc())
        query = query.offset(offset).limit(page_size)

        models = self.session.execute(query).scalars().all()
        return [self._to_gdpr_request_entity(m) for m in models], total

    def anonymize_actor_email(
        self, actor_id: str, anonymized_email: str
    ) -> int:
        result = self.session.execute(
            update(AuditEntryModel)
            .where(AuditEntryModel.actor_id == actor_id)
            .values(actor_email=anonymized_email)
        )
        self.session.flush()
        return result.rowcount  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # RetentionPolicy
    # ------------------------------------------------------------------

    def save_retention_policy(self, policy: RetentionPolicy) -> None:
        existing = self.session.execute(
            select(RetentionPolicyModel).where(
                RetentionPolicyModel.company_id == policy.company_id
            )
        ).scalar_one_or_none()
        if existing:
            existing.retention_months = policy.retention_months
            existing.updated_at = policy.updated_at  # type: ignore[assignment]
            existing.updated_by = policy.updated_by
        else:
            model = RetentionPolicyModel(
                id=policy.id,
                company_id=policy.company_id,
                retention_months=policy.retention_months,
                updated_at=policy.updated_at,
                updated_by=policy.updated_by,
            )
            self.session.add(model)
        self.session.flush()

    def find_retention_policy(
        self, company_id: str
    ) -> Optional[RetentionPolicy]:
        model = self.session.execute(
            select(RetentionPolicyModel).where(
                RetentionPolicyModel.company_id == company_id
            )
        ).scalar_one_or_none()
        if model is None:
            return None
        return self._to_retention_policy_entity(model)

    def find_all_retention_policies(self) -> list[RetentionPolicy]:
        models = self.session.execute(
            select(RetentionPolicyModel).where(
                RetentionPolicyModel.retention_months > 0
            )
        ).scalars().all()
        return [self._to_retention_policy_entity(m) for m in models]

    def delete_entries_before(
        self, company_id: str, before: datetime
    ) -> int:
        result = self.session.execute(
            delete(AuditEntryModel).where(
                AuditEntryModel.company_id == company_id,
                AuditEntryModel.created_at < before,
            )
        )
        self.session.flush()
        return result.rowcount  # type: ignore[return-value]

    def find_entries_for_verification(
        self,
        company_id: str,
        date_from: datetime,
        date_to: datetime,
        page: int,
        page_size: int,
    ) -> list[AuditEntry]:
        offset = (page - 1) * page_size
        stmt = (
            select(AuditEntryModel)
            .where(
                AuditEntryModel.company_id == company_id,
                AuditEntryModel.created_at >= date_from,
                AuditEntryModel.created_at <= date_to,
            )
            .order_by(AuditEntryModel.created_at.asc())
            .offset(offset)
            .limit(page_size)
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def _to_retention_policy_entity(
        self, model: RetentionPolicyModel
    ) -> RetentionPolicy:
        return RetentionPolicy(
            id=model.id,
            company_id=model.company_id,
            retention_months=model.retention_months,
            updated_at=model.updated_at,
            updated_by=model.updated_by,
        )

    def _to_gdpr_request_entity(
        self, model: GdprRequestModel
    ) -> GdprRequest:
        return GdprRequest(
            id=model.id,
            company_id=model.company_id,
            target_user_id=model.target_user_id,
            target_user_email=model.target_user_email,
            requested_by=model.requested_by,
            request_type=GdprRequestType(model.request_type),
            status=GdprRequestStatus(model.status),
            reason=model.reason,
            storage_key=model.storage_key,
            error_message=model.error_message,
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
        )

    # ------------------------------------------------------------------
    # ComplianceAssessment
    # ------------------------------------------------------------------

    def save_assessment(self, assessment: ComplianceAssessment) -> None:
        existing = self.session.execute(
            select(ComplianceAssessmentModel).where(
                ComplianceAssessmentModel.company_id == assessment.company_id,
                ComplianceAssessmentModel.control_id == assessment.control_id,
            )
        ).scalar_one_or_none()
        if existing:
            existing.status = assessment.status.value
            existing.notes = assessment.notes
            existing.assessed_by = assessment.assessed_by
            existing.assessed_at = assessment.assessed_at  # type: ignore[assignment]
            existing.updated_at = assessment.updated_at  # type: ignore[assignment]
        else:
            model = ComplianceAssessmentModel(
                id=assessment.id,
                company_id=assessment.company_id,
                control_id=assessment.control_id,
                status=assessment.status.value,
                notes=assessment.notes,
                assessed_by=assessment.assessed_by,
                assessed_at=assessment.assessed_at,
                created_at=assessment.created_at,
                updated_at=assessment.updated_at,
            )
            self.session.add(model)
        self.session.flush()

    def find_assessment(
        self, company_id: str, control_id: str
    ) -> Optional[ComplianceAssessment]:
        model = self.session.execute(
            select(ComplianceAssessmentModel).where(
                ComplianceAssessmentModel.company_id == company_id,
                ComplianceAssessmentModel.control_id == control_id,
            )
        ).scalar_one_or_none()
        if model is None:
            return None
        return self._to_assessment_entity(model)

    def find_assessments_by_company(
        self, company_id: str
    ) -> list[ComplianceAssessment]:
        models = self.session.execute(
            select(ComplianceAssessmentModel).where(
                ComplianceAssessmentModel.company_id == company_id
            )
        ).scalars().all()
        return [self._to_assessment_entity(m) for m in models]

    def count_assessments_by_status(
        self, company_id: str, framework: Optional[str] = None
    ) -> dict[str, int]:
        stmt = (
            select(
                ComplianceAssessmentModel.status,
                func.count(ComplianceAssessmentModel.id),
            )
            .where(ComplianceAssessmentModel.company_id == company_id)
            .group_by(ComplianceAssessmentModel.status)
        )
        if framework:
            stmt = stmt.join(
                ComplianceControlModel,
                ComplianceAssessmentModel.control_id
                == ComplianceControlModel.id,
            ).where(ComplianceControlModel.framework == framework)
        rows = self.session.execute(stmt).all()
        return {row[0]: row[1] for row in rows}

    # ------------------------------------------------------------------
    # ComplianceEvidence
    # ------------------------------------------------------------------

    def save_evidence(self, evidence: ComplianceEvidence) -> None:
        model = ComplianceEvidenceModel(
            id=evidence.id,
            company_id=evidence.company_id,
            control_id=evidence.control_id,
            evidence_type=evidence.evidence_type.value,
            reference_id=evidence.reference_id,
            title=evidence.title,
            description=evidence.description,
            url=evidence.url,
            added_by=evidence.added_by,
            created_at=evidence.created_at,
        )
        self.session.add(model)
        self.session.flush()

    def find_evidence_by_id(
        self, evidence_id: str, company_id: str
    ) -> Optional[ComplianceEvidence]:
        model = self.session.execute(
            select(ComplianceEvidenceModel).where(
                ComplianceEvidenceModel.id == evidence_id,
                ComplianceEvidenceModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        if model is None:
            return None
        return self._to_evidence_entity(model)

    def find_evidence_by_control(
        self, control_id: str, company_id: str
    ) -> list[ComplianceEvidence]:
        models = self.session.execute(
            select(ComplianceEvidenceModel)
            .where(
                ComplianceEvidenceModel.control_id == control_id,
                ComplianceEvidenceModel.company_id == company_id,
            )
            .order_by(ComplianceEvidenceModel.created_at.desc())
        ).scalars().all()
        return [self._to_evidence_entity(m) for m in models]

    def count_evidence_by_control(
        self, company_id: str
    ) -> dict[str, int]:
        rows = self.session.execute(
            select(
                ComplianceEvidenceModel.control_id,
                func.count(ComplianceEvidenceModel.id),
            )
            .where(ComplianceEvidenceModel.company_id == company_id)
            .group_by(ComplianceEvidenceModel.control_id)
        ).all()
        return {row[0]: row[1] for row in rows}

    def delete_evidence(self, evidence_id: str) -> None:
        self.session.execute(
            delete(ComplianceEvidenceModel).where(
                ComplianceEvidenceModel.id == evidence_id
            )
        )
        self.session.flush()

    def _to_assessment_entity(
        self, model: ComplianceAssessmentModel
    ) -> ComplianceAssessment:
        return ComplianceAssessment(
            id=model.id,
            company_id=model.company_id,
            control_id=model.control_id,
            status=ComplianceStatus(model.status),
            notes=model.notes,
            assessed_by=model.assessed_by,
            assessed_at=model.assessed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_evidence_entity(
        self, model: ComplianceEvidenceModel
    ) -> ComplianceEvidence:
        return ComplianceEvidence(
            id=model.id,
            company_id=model.company_id,
            control_id=model.control_id,
            evidence_type=EvidenceType(model.evidence_type),
            reference_id=model.reference_id,
            title=model.title,
            description=model.description,
            url=model.url,
            added_by=model.added_by,
            created_at=model.created_at,
        )
