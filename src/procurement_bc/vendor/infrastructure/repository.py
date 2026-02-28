import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.procurement_bc.vendor.domain.entities import (
    Vendor,
    VendorContract,
    VendorContractDocument,
    VendorDependency,
    VendorRiskAssessment,
)
from src.procurement_bc.vendor.domain.enums import (
    BusinessFunction,
    ContractStatus,
    ContractType,
    VendorCategory,
    VendorRiskLevel,
)
from src.procurement_bc.vendor.domain.repository import (
    VendorRepositoryInterface,
    VendorContractRepositoryInterface,
    VendorContractDocumentRepositoryInterface,
    VendorDependencyRepositoryInterface,
    VendorRiskAssessmentRepositoryInterface,
)
from src.procurement_bc.vendor.infrastructure.models import (
    VendorModel,
    VendorContractModel,
    VendorContractDocumentModel,
    VendorDependencyModel,
    VendorRiskAssessmentModel,
)

logger = logging.getLogger(__name__)


class VendorRepository(VendorRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, vendor: Vendor) -> Vendor:
        existing = self.session.execute(
            select(VendorModel).where(
                VendorModel.id == vendor.id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.name = vendor.name
            existing.contact_email = vendor.contact_email
            existing.phone = vendor.phone
            existing.address = vendor.address
            existing.notes = vendor.notes
            existing.is_active = vendor.is_active
            existing.is_critical_ict = vendor.is_critical_ict
            existing.risk_level = vendor.risk_level.value if vendor.risk_level else None
            existing.website = vendor.website
            existing.category = vendor.category.value if vendor.category else None
        else:
            model = VendorModel(
                id=vendor.id,
                company_id=vendor.company_id,
                name=vendor.name,
                contact_email=vendor.contact_email,
                phone=vendor.phone,
                address=vendor.address,
                notes=vendor.notes,
                is_active=vendor.is_active,
                is_critical_ict=vendor.is_critical_ict,
                risk_level=vendor.risk_level.value if vendor.risk_level else None,
                website=vendor.website,
                category=vendor.category.value if vendor.category else None,
            )
            self.session.add(model)

        self.session.flush()
        return vendor

    def find_by_id(
        self, vendor_id: str, company_id: str,
    ) -> Optional[Vendor]:
        model = self.session.execute(
            select(VendorModel).where(
                VendorModel.id == vendor_id,
                VendorModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Vendor], int]:
        stmt = select(VendorModel).where(
            VendorModel.company_id == company_id,
        )
        if search:
            stmt = stmt.where(
                VendorModel.name.ilike(f"%{search}%"),
            )
        if is_active is not None:
            stmt = stmt.where(
                VendorModel.is_active == is_active,
            )

        total = self.session.execute(
            select(func.count()).select_from(
                stmt.subquery(),
            )
        ).scalar()

        models = (
            self.session.execute(
                stmt.order_by(VendorModel.name)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
        return (
            [self._to_entity(m) for m in models],
            total or 0,
        )

    def find_by_name(
        self, name: str, company_id: str,
    ) -> Optional[Vendor]:
        model = self.session.execute(
            select(VendorModel).where(
                VendorModel.name == name,
                VendorModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(model: VendorModel) -> Vendor:
        return Vendor(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            is_active=model.is_active,
            contact_email=model.contact_email,
            phone=model.phone,
            address=model.address,
            notes=model.notes,
            is_critical_ict=model.is_critical_ict,
            risk_level=VendorRiskLevel(model.risk_level) if model.risk_level else None,
            website=model.website,
            category=VendorCategory(model.category) if model.category else None,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class VendorContractRepository(VendorContractRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, contract: VendorContract) -> VendorContract:
        existing = self.session.execute(
            select(VendorContractModel).where(
                VendorContractModel.id == contract.id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.contract_type = contract.contract_type.value
            existing.title = contract.title
            existing.start_date = contract.start_date
            existing.end_date = contract.end_date
            existing.renewal_date = contract.renewal_date
            existing.auto_renewal = contract.auto_renewal
            existing.annual_value = contract.annual_value
            existing.currency = contract.currency
            existing.security_clauses = contract.security_clauses
            existing.notes = contract.notes
            existing.status = contract.status.value
            existing.is_deleted = contract.is_deleted
        else:
            model = VendorContractModel(
                id=contract.id,
                vendor_id=contract.vendor_id,
                company_id=contract.company_id,
                contract_type=contract.contract_type.value,
                title=contract.title,
                start_date=contract.start_date,
                end_date=contract.end_date,
                renewal_date=contract.renewal_date,
                auto_renewal=contract.auto_renewal,
                annual_value=contract.annual_value,
                currency=contract.currency,
                security_clauses=contract.security_clauses,
                notes=contract.notes,
                status=contract.status.value,
                is_deleted=contract.is_deleted,
            )
            self.session.add(model)

        self.session.flush()
        return contract

    def find_by_id(
        self, contract_id: str, vendor_id: str, company_id: str,
    ) -> Optional[VendorContract]:
        model = self.session.execute(
            select(VendorContractModel).where(
                VendorContractModel.id == contract_id,
                VendorContractModel.vendor_id == vendor_id,
                VendorContractModel.company_id == company_id,
                VendorContractModel.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all_by_vendor(
        self,
        vendor_id: str,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[ContractStatus] = None,
    ) -> tuple[list[VendorContract], int]:
        stmt = select(VendorContractModel).where(
            VendorContractModel.vendor_id == vendor_id,
            VendorContractModel.company_id == company_id,
            VendorContractModel.is_deleted.is_(False),
        )
        if status:
            stmt = stmt.where(VendorContractModel.status == status.value)

        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()

        models = (
            self.session.execute(
                stmt.order_by(VendorContractModel.start_date.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models], total or 0

    def soft_delete(
        self, contract_id: str, vendor_id: str, company_id: str,
    ) -> None:
        model = self.session.execute(
            select(VendorContractModel).where(
                VendorContractModel.id == contract_id,
                VendorContractModel.vendor_id == vendor_id,
                VendorContractModel.company_id == company_id,
                VendorContractModel.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if model:
            model.is_deleted = True
            self.session.flush()

    def find_expired_active_contracts(self) -> list[VendorContract]:
        today = date.today()
        models = (
            self.session.execute(
                select(VendorContractModel).where(
                    VendorContractModel.status == ContractStatus.ACTIVE.value,
                    VendorContractModel.end_date.isnot(None),
                    VendorContractModel.end_date < today,
                    VendorContractModel.is_deleted.is_(False),
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def has_active_contract_with_security_clauses(
        self, vendor_id: str, company_id: str,
    ) -> bool:
        model = self.session.execute(
            select(VendorContractModel).where(
                VendorContractModel.vendor_id == vendor_id,
                VendorContractModel.company_id == company_id,
                VendorContractModel.status == ContractStatus.ACTIVE.value,
                VendorContractModel.is_deleted.is_(False),
                VendorContractModel.security_clauses.isnot(None),
            ).limit(1)
        ).scalar_one_or_none()
        if not model or not model.security_clauses:
            return False
        return any(model.security_clauses.values())

    @staticmethod
    def _to_entity(model: VendorContractModel) -> VendorContract:
        return VendorContract(
            id=model.id,
            vendor_id=model.vendor_id,
            company_id=model.company_id,
            contract_type=ContractType(model.contract_type),
            title=model.title,
            start_date=model.start_date,
            status=ContractStatus(model.status),
            end_date=model.end_date,
            renewal_date=model.renewal_date,
            auto_renewal=model.auto_renewal,
            annual_value=Decimal(str(model.annual_value)) if model.annual_value is not None else None,
            currency=model.currency,
            security_clauses=model.security_clauses or {},
            notes=model.notes,
            is_deleted=model.is_deleted,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class VendorContractDocumentRepository(VendorContractDocumentRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, document: VendorContractDocument) -> VendorContractDocument:
        model = VendorContractDocumentModel(
            id=document.id,
            contract_id=document.contract_id,
            company_id=document.company_id,
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            storage_key=document.storage_key,
            uploaded_by=document.uploaded_by,
            is_deleted=document.is_deleted,
        )
        self.session.add(model)
        self.session.flush()
        return document

    def find_by_id(
        self, document_id: str, contract_id: str, company_id: str,
    ) -> Optional[VendorContractDocument]:
        model = self.session.execute(
            select(VendorContractDocumentModel).where(
                VendorContractDocumentModel.id == document_id,
                VendorContractDocumentModel.contract_id == contract_id,
                VendorContractDocumentModel.company_id == company_id,
                VendorContractDocumentModel.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all_by_contract(
        self, contract_id: str, company_id: str,
    ) -> list[VendorContractDocument]:
        models = (
            self.session.execute(
                select(VendorContractDocumentModel).where(
                    VendorContractDocumentModel.contract_id == contract_id,
                    VendorContractDocumentModel.company_id == company_id,
                    VendorContractDocumentModel.is_deleted.is_(False),
                ).order_by(VendorContractDocumentModel.created_at.desc())
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def soft_delete(
        self, document_id: str, contract_id: str, company_id: str,
    ) -> None:
        model = self.session.execute(
            select(VendorContractDocumentModel).where(
                VendorContractDocumentModel.id == document_id,
                VendorContractDocumentModel.contract_id == contract_id,
                VendorContractDocumentModel.company_id == company_id,
                VendorContractDocumentModel.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if model:
            model.is_deleted = True
            self.session.flush()

    def count_by_contract(
        self, contract_id: str, company_id: str,
    ) -> int:
        result = self.session.execute(
            select(func.count()).where(
                VendorContractDocumentModel.contract_id == contract_id,
                VendorContractDocumentModel.company_id == company_id,
                VendorContractDocumentModel.is_deleted.is_(False),
            )
        ).scalar()
        return result or 0

    @staticmethod
    def _to_entity(model: VendorContractDocumentModel) -> VendorContractDocument:
        return VendorContractDocument(
            id=model.id,
            contract_id=model.contract_id,
            company_id=model.company_id,
            filename=model.filename,
            content_type=model.content_type,
            size_bytes=model.size_bytes,
            storage_key=model.storage_key,
            uploaded_by=model.uploaded_by,
            is_deleted=model.is_deleted,
            created_at=model.created_at,
        )


class VendorRiskAssessmentRepository(VendorRiskAssessmentRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(
        self, assessment: VendorRiskAssessment,
    ) -> VendorRiskAssessment:
        existing = self.session.execute(
            select(VendorRiskAssessmentModel).where(
                VendorRiskAssessmentModel.id == assessment.id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.assessment_date = assessment.assessment_date
            existing.next_review_date = assessment.next_review_date
            existing.data_handling_score = assessment.data_handling_score
            existing.security_certs_score = assessment.security_certs_score
            existing.incident_response_score = assessment.incident_response_score
            existing.business_continuity_score = assessment.business_continuity_score
            existing.subcontractor_score = assessment.subcontractor_score
            existing.overall_risk_level = assessment.overall_risk_level.value
            existing.justification = assessment.justification
            existing.is_deleted = assessment.is_deleted
        else:
            model = VendorRiskAssessmentModel(
                id=assessment.id,
                vendor_id=assessment.vendor_id,
                company_id=assessment.company_id,
                assessed_by=assessment.assessed_by,
                assessment_date=assessment.assessment_date,
                next_review_date=assessment.next_review_date,
                data_handling_score=assessment.data_handling_score,
                security_certs_score=assessment.security_certs_score,
                incident_response_score=assessment.incident_response_score,
                business_continuity_score=assessment.business_continuity_score,
                subcontractor_score=assessment.subcontractor_score,
                overall_risk_level=assessment.overall_risk_level.value,
                justification=assessment.justification,
                is_deleted=assessment.is_deleted,
            )
            self.session.add(model)

        self.session.flush()
        return assessment

    def find_by_id(
        self, assessment_id: str, vendor_id: str, company_id: str,
    ) -> Optional[VendorRiskAssessment]:
        model = self.session.execute(
            select(VendorRiskAssessmentModel).where(
                VendorRiskAssessmentModel.id == assessment_id,
                VendorRiskAssessmentModel.vendor_id == vendor_id,
                VendorRiskAssessmentModel.company_id == company_id,
                VendorRiskAssessmentModel.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all_by_vendor(
        self,
        vendor_id: str,
        company_id: str,
        page: int,
        page_size: int,
    ) -> tuple[list[VendorRiskAssessment], int]:
        stmt = select(VendorRiskAssessmentModel).where(
            VendorRiskAssessmentModel.vendor_id == vendor_id,
            VendorRiskAssessmentModel.company_id == company_id,
            VendorRiskAssessmentModel.is_deleted.is_(False),
        )

        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()

        models = (
            self.session.execute(
                stmt.order_by(
                    VendorRiskAssessmentModel.assessment_date.desc(),
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models], total or 0

    def find_latest_by_vendor(
        self, vendor_id: str, company_id: str,
    ) -> Optional[VendorRiskAssessment]:
        model = self.session.execute(
            select(VendorRiskAssessmentModel).where(
                VendorRiskAssessmentModel.vendor_id == vendor_id,
                VendorRiskAssessmentModel.company_id == company_id,
                VendorRiskAssessmentModel.is_deleted.is_(False),
            ).order_by(
                VendorRiskAssessmentModel.assessment_date.desc(),
            ).limit(1)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def soft_delete(
        self, assessment_id: str, vendor_id: str, company_id: str,
    ) -> None:
        model = self.session.execute(
            select(VendorRiskAssessmentModel).where(
                VendorRiskAssessmentModel.id == assessment_id,
                VendorRiskAssessmentModel.vendor_id == vendor_id,
                VendorRiskAssessmentModel.company_id == company_id,
                VendorRiskAssessmentModel.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if model:
            model.is_deleted = True
            self.session.flush()

    def find_vendors_with_stale_assessments(
        self, company_id: str, as_of: date,
    ) -> list[str]:
        from sqlalchemy import and_

        subq = (
            select(
                VendorRiskAssessmentModel.vendor_id,
                func.max(VendorRiskAssessmentModel.assessment_date).label(
                    "latest_date",
                ),
            )
            .where(
                VendorRiskAssessmentModel.company_id == company_id,
                VendorRiskAssessmentModel.is_deleted.is_(False),
            )
            .group_by(VendorRiskAssessmentModel.vendor_id)
            .subquery()
        )

        latest = self.session.execute(
            select(VendorRiskAssessmentModel).where(
                VendorRiskAssessmentModel.company_id == company_id,
                VendorRiskAssessmentModel.is_deleted.is_(False),
                VendorRiskAssessmentModel.next_review_date.isnot(None),
                VendorRiskAssessmentModel.next_review_date < as_of,
                and_(
                    VendorRiskAssessmentModel.vendor_id == subq.c.vendor_id,
                    VendorRiskAssessmentModel.assessment_date == subq.c.latest_date,
                ),
            )
        ).scalars().all()

        return list({m.vendor_id for m in latest})

    @staticmethod
    def _to_entity(
        model: VendorRiskAssessmentModel,
    ) -> VendorRiskAssessment:
        return VendorRiskAssessment(
            id=model.id,
            vendor_id=model.vendor_id,
            company_id=model.company_id,
            assessed_by=model.assessed_by,
            assessment_date=model.assessment_date,
            data_handling_score=model.data_handling_score,
            security_certs_score=model.security_certs_score,
            incident_response_score=model.incident_response_score,
            business_continuity_score=model.business_continuity_score,
            subcontractor_score=model.subcontractor_score,
            overall_risk_level=VendorRiskLevel(model.overall_risk_level),
            next_review_date=model.next_review_date,
            justification=model.justification,
            is_deleted=model.is_deleted,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class VendorDependencyRepository(VendorDependencyRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(
        self, dependency: VendorDependency,
    ) -> VendorDependency:
        existing = self.session.execute(
            select(VendorDependencyModel).where(
                VendorDependencyModel.id == dependency.id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.service_description = dependency.service_description
            existing.business_function = dependency.business_function.value
            existing.is_critical = dependency.is_critical
            existing.notes = dependency.notes
            existing.is_deleted = dependency.is_deleted
        else:
            model = VendorDependencyModel(
                id=dependency.id,
                vendor_id=dependency.vendor_id,
                company_id=dependency.company_id,
                service_description=dependency.service_description,
                business_function=dependency.business_function.value,
                is_critical=dependency.is_critical,
                notes=dependency.notes,
                is_deleted=dependency.is_deleted,
            )
            self.session.add(model)

        self.session.flush()
        return dependency

    def find_by_id(
        self, dependency_id: str, vendor_id: str, company_id: str,
    ) -> Optional[VendorDependency]:
        model = self.session.execute(
            select(VendorDependencyModel).where(
                VendorDependencyModel.id == dependency_id,
                VendorDependencyModel.vendor_id == vendor_id,
                VendorDependencyModel.company_id == company_id,
                VendorDependencyModel.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all_by_vendor(
        self,
        vendor_id: str,
        company_id: str,
        page: int,
        page_size: int,
    ) -> tuple[list[VendorDependency], int]:
        stmt = select(VendorDependencyModel).where(
            VendorDependencyModel.vendor_id == vendor_id,
            VendorDependencyModel.company_id == company_id,
            VendorDependencyModel.is_deleted.is_(False),
        )

        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()

        models = (
            self.session.execute(
                stmt.order_by(
                    VendorDependencyModel.created_at.desc(),
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models], total or 0

    def soft_delete(
        self, dependency_id: str, vendor_id: str, company_id: str,
    ) -> None:
        model = self.session.execute(
            select(VendorDependencyModel).where(
                VendorDependencyModel.id == dependency_id,
                VendorDependencyModel.vendor_id == vendor_id,
                VendorDependencyModel.company_id == company_id,
                VendorDependencyModel.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if model:
            model.is_deleted = True
            self.session.flush()

    def find_all_critical_by_company(
        self, company_id: str,
    ) -> list[VendorDependency]:
        models = (
            self.session.execute(
                select(VendorDependencyModel).where(
                    VendorDependencyModel.company_id == company_id,
                    VendorDependencyModel.is_critical.is_(True),
                    VendorDependencyModel.is_deleted.is_(False),
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    @staticmethod
    def _to_entity(
        model: VendorDependencyModel,
    ) -> VendorDependency:
        return VendorDependency(
            id=model.id,
            vendor_id=model.vendor_id,
            company_id=model.company_id,
            service_description=model.service_description,
            business_function=BusinessFunction(model.business_function),
            is_critical=model.is_critical,
            notes=model.notes,
            is_deleted=model.is_deleted,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
