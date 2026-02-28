import pytest
from datetime import date
from decimal import Decimal

from src.procurement_bc.vendor.domain.entities import (
    Vendor,
    VendorContract,
    VendorContractDocument,
)
from src.procurement_bc.vendor.domain.enums import (
    ContractStatus,
    ContractType,
    VendorCategory,
)
from src.procurement_bc.vendor.domain.exceptions import (
    InvalidContractTransitionError,
)


class TestVendorExtendedFields:
    def test_update_extended_fields(self):
        vendor = Vendor.create(
            company_id="comp1", name="Acme",
        )
        vendor.update_extended_fields(
            category=VendorCategory.SAAS,
            website="https://acme.com",
            is_critical_ict=True,
        )
        assert vendor.category == VendorCategory.SAAS
        assert vendor.website == "https://acme.com"
        assert vendor.is_critical_ict is True

    def test_update_extended_fields_partial(self):
        vendor = Vendor.create(
            company_id="comp1", name="Acme",
        )
        vendor.update_extended_fields(
            category=VendorCategory.HARDWARE,
        )
        assert vendor.category == VendorCategory.HARDWARE
        assert vendor.website is None
        assert vendor.is_critical_ict is False

    def test_update_extended_fields_none_no_change(self):
        vendor = Vendor.create(
            company_id="comp1", name="Acme",
        )
        vendor.update_extended_fields(
            category=VendorCategory.CLOUD,
        )
        vendor.update_extended_fields(
            website="https://cloud.com",
        )
        assert vendor.category == VendorCategory.CLOUD
        assert vendor.website == "https://cloud.com"


class TestVendorContractCreate:
    def test_creates_contract(self):
        contract = VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SAAS,
            title="SaaS License",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            annual_value=Decimal("12000.00"),
            currency="EUR",
        )
        assert contract.id is not None
        assert len(contract.id) == 26
        assert contract.status == ContractStatus.DRAFT
        assert contract.title == "SaaS License"
        assert contract.annual_value == Decimal("12000.00")

    def test_strips_title(self):
        contract = VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SERVICE,
            title="  Support  ",
            start_date=date(2026, 1, 1),
        )
        assert contract.title == "Support"

    def test_empty_title_raises(self):
        with pytest.raises(ValueError, match="title"):
            VendorContract.create(
                vendor_id="v1",
                company_id="comp1",
                contract_type=ContractType.SERVICE,
                title="",
                start_date=date(2026, 1, 1),
            )

    def test_default_security_clauses_empty(self):
        contract = VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SUPPLY,
            title="Hardware Supply",
            start_date=date(2026, 1, 1),
        )
        assert contract.security_clauses == {}

    def test_custom_security_clauses(self):
        clauses = {
            "data_protection": True,
            "incident_notification": True,
        }
        contract = VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SERVICE,
            title="Secure Service",
            start_date=date(2026, 1, 1),
            security_clauses=clauses,
        )
        assert contract.security_clauses == clauses


class TestVendorContractStatusTransitions:
    def _make_contract(
        self, status: ContractStatus = ContractStatus.DRAFT,
    ) -> VendorContract:
        contract = VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SERVICE,
            title="Test",
            start_date=date(2026, 1, 1),
        )
        contract.status = status
        return contract

    def test_draft_to_active(self):
        contract = self._make_contract(ContractStatus.DRAFT)
        contract.change_status(ContractStatus.ACTIVE)
        assert contract.status == ContractStatus.ACTIVE

    def test_draft_to_terminated(self):
        contract = self._make_contract(ContractStatus.DRAFT)
        contract.change_status(ContractStatus.TERMINATED)
        assert contract.status == ContractStatus.TERMINATED

    def test_active_to_expired(self):
        contract = self._make_contract(ContractStatus.ACTIVE)
        contract.change_status(ContractStatus.EXPIRED)
        assert contract.status == ContractStatus.EXPIRED

    def test_active_to_terminated(self):
        contract = self._make_contract(ContractStatus.ACTIVE)
        contract.change_status(ContractStatus.TERMINATED)
        assert contract.status == ContractStatus.TERMINATED

    def test_expired_to_active(self):
        contract = self._make_contract(ContractStatus.EXPIRED)
        contract.change_status(ContractStatus.ACTIVE)
        assert contract.status == ContractStatus.ACTIVE

    def test_terminated_to_draft(self):
        contract = self._make_contract(ContractStatus.TERMINATED)
        contract.change_status(ContractStatus.DRAFT)
        assert contract.status == ContractStatus.DRAFT

    def test_draft_to_expired_invalid(self):
        contract = self._make_contract(ContractStatus.DRAFT)
        with pytest.raises(InvalidContractTransitionError):
            contract.change_status(ContractStatus.EXPIRED)

    def test_active_to_draft_invalid(self):
        contract = self._make_contract(ContractStatus.ACTIVE)
        with pytest.raises(InvalidContractTransitionError):
            contract.change_status(ContractStatus.DRAFT)

    def test_expired_to_terminated_invalid(self):
        contract = self._make_contract(ContractStatus.EXPIRED)
        with pytest.raises(InvalidContractTransitionError):
            contract.change_status(ContractStatus.TERMINATED)

    def test_terminated_to_active_invalid(self):
        contract = self._make_contract(ContractStatus.TERMINATED)
        with pytest.raises(InvalidContractTransitionError):
            contract.change_status(ContractStatus.ACTIVE)


class TestVendorContractUpdate:
    def test_update_fields(self):
        contract = VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SERVICE,
            title="Original",
            start_date=date(2026, 1, 1),
        )
        contract.update(
            title="Updated",
            annual_value=Decimal("5000.00"),
            currency="USD",
            notes="New notes",
        )
        assert contract.title == "Updated"
        assert contract.annual_value == Decimal("5000.00")
        assert contract.currency == "USD"
        assert contract.notes == "New notes"

    def test_update_empty_title_raises(self):
        contract = VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SERVICE,
            title="Test",
            start_date=date(2026, 1, 1),
        )
        with pytest.raises(ValueError, match="title"):
            contract.update(title="  ")

    def test_update_none_keeps_current(self):
        contract = VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SERVICE,
            title="Keep",
            start_date=date(2026, 1, 1),
            notes="Keep this",
        )
        contract.update(annual_value=Decimal("100"))
        assert contract.title == "Keep"
        assert contract.notes == "Keep this"
        assert contract.annual_value == Decimal("100")


class TestVendorContractSoftDelete:
    def test_soft_delete(self):
        contract = VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SERVICE,
            title="Test",
            start_date=date(2026, 1, 1),
        )
        assert contract.is_deleted is False
        contract.soft_delete()
        assert contract.is_deleted is True


class TestVendorContractDocument:
    def test_creates_document(self):
        doc = VendorContractDocument.create(
            contract_id="c1",
            company_id="comp1",
            filename="contract.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            storage_key="comp1/v1/c1/d1/contract.pdf",
            uploaded_by="user1",
        )
        assert doc.id is not None
        assert doc.filename == "contract.pdf"
        assert doc.is_deleted is False

    def test_empty_filename_raises(self):
        with pytest.raises(ValueError, match="Filename"):
            VendorContractDocument.create(
                contract_id="c1",
                company_id="comp1",
                filename="",
                content_type="application/pdf",
                size_bytes=1024,
                storage_key="key",
                uploaded_by="user1",
            )

    def test_soft_delete(self):
        doc = VendorContractDocument.create(
            contract_id="c1",
            company_id="comp1",
            filename="doc.pdf",
            content_type="application/pdf",
            size_bytes=512,
            storage_key="key",
            uploaded_by="user1",
        )
        doc.soft_delete()
        assert doc.is_deleted is True
