from abc import ABC, abstractmethod
from typing import Optional

from datetime import date

from src.procurement_bc.vendor.domain.entities import (
    Vendor,
    VendorContract,
    VendorContractDocument,
    VendorDependency,
    VendorRiskAssessment,
)
from src.procurement_bc.vendor.domain.enums import ContractStatus


class VendorRepositoryInterface(ABC):

    @abstractmethod
    def save(self, vendor: Vendor) -> Vendor: ...

    @abstractmethod
    def find_by_id(
        self, vendor_id: str, company_id: str,
    ) -> Optional[Vendor]: ...

    @abstractmethod
    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Vendor], int]: ...

    @abstractmethod
    def find_by_name(
        self, name: str, company_id: str,
    ) -> Optional[Vendor]: ...


class VendorContractRepositoryInterface(ABC):

    @abstractmethod
    def save(self, contract: VendorContract) -> VendorContract: ...

    @abstractmethod
    def find_by_id(
        self, contract_id: str, vendor_id: str, company_id: str,
    ) -> Optional[VendorContract]: ...

    @abstractmethod
    def find_all_by_vendor(
        self,
        vendor_id: str,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[ContractStatus] = None,
    ) -> tuple[list[VendorContract], int]: ...

    @abstractmethod
    def soft_delete(
        self, contract_id: str, vendor_id: str, company_id: str,
    ) -> None: ...

    @abstractmethod
    def find_expired_active_contracts(self) -> list[VendorContract]: ...

    @abstractmethod
    def has_active_contract_with_security_clauses(
        self, vendor_id: str, company_id: str,
    ) -> bool: ...


class VendorContractDocumentRepositoryInterface(ABC):

    @abstractmethod
    def save(self, document: VendorContractDocument) -> VendorContractDocument: ...

    @abstractmethod
    def find_by_id(
        self, document_id: str, contract_id: str, company_id: str,
    ) -> Optional[VendorContractDocument]: ...

    @abstractmethod
    def find_all_by_contract(
        self, contract_id: str, company_id: str,
    ) -> list[VendorContractDocument]: ...

    @abstractmethod
    def soft_delete(
        self, document_id: str, contract_id: str, company_id: str,
    ) -> None: ...

    @abstractmethod
    def count_by_contract(
        self, contract_id: str, company_id: str,
    ) -> int: ...


class VendorRiskAssessmentRepositoryInterface(ABC):

    @abstractmethod
    def save(
        self, assessment: VendorRiskAssessment,
    ) -> VendorRiskAssessment: ...

    @abstractmethod
    def find_by_id(
        self, assessment_id: str, vendor_id: str, company_id: str,
    ) -> Optional[VendorRiskAssessment]: ...

    @abstractmethod
    def find_all_by_vendor(
        self,
        vendor_id: str,
        company_id: str,
        page: int,
        page_size: int,
    ) -> tuple[list[VendorRiskAssessment], int]: ...

    @abstractmethod
    def find_latest_by_vendor(
        self, vendor_id: str, company_id: str,
    ) -> Optional[VendorRiskAssessment]: ...

    @abstractmethod
    def soft_delete(
        self, assessment_id: str, vendor_id: str, company_id: str,
    ) -> None: ...

    @abstractmethod
    def find_vendors_with_stale_assessments(
        self, company_id: str, as_of: date,
    ) -> list[str]: ...


class VendorDependencyRepositoryInterface(ABC):

    @abstractmethod
    def save(
        self, dependency: VendorDependency,
    ) -> VendorDependency: ...

    @abstractmethod
    def find_by_id(
        self, dependency_id: str, vendor_id: str, company_id: str,
    ) -> Optional[VendorDependency]: ...

    @abstractmethod
    def find_all_by_vendor(
        self,
        vendor_id: str,
        company_id: str,
        page: int,
        page_size: int,
    ) -> tuple[list[VendorDependency], int]: ...

    @abstractmethod
    def soft_delete(
        self, dependency_id: str, vendor_id: str, company_id: str,
    ) -> None: ...

    @abstractmethod
    def find_all_critical_by_company(
        self, company_id: str,
    ) -> list[VendorDependency]: ...
