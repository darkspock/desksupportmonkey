import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from src.procurement_bc.vendor.application.commands.create_contract import (
    CreateContractCommand,
    CreateContractCommandHandler,
)
from src.procurement_bc.vendor.application.commands.update_contract import (
    UpdateContractCommand,
    UpdateContractCommandHandler,
)
from src.procurement_bc.vendor.application.commands.change_contract_status import (
    ChangeContractStatusCommand,
    ChangeContractStatusCommandHandler,
)
from src.procurement_bc.vendor.application.commands.soft_delete_contract import (
    SoftDeleteContractCommand,
    SoftDeleteContractCommandHandler,
)
from src.procurement_bc.vendor.domain.entities import VendorContract
from src.procurement_bc.vendor.domain.enums import (
    ContractStatus,
    ContractType,
)
from src.procurement_bc.vendor.domain.exceptions import (
    ContractNotFoundError,
    InvalidContractTransitionError,
    VendorNotFoundError,
)


class TestCreateContractCommandHandler:
    def setup_method(self):
        self.vendor_repo = MagicMock()
        self.contract_repo = MagicMock()
        self.handler = CreateContractCommandHandler(
            vendor_repo=self.vendor_repo,
            contract_repo=self.contract_repo,
        )

    def test_creates_contract(self):
        self.vendor_repo.find_by_id.return_value = MagicMock()
        self.handler.handle(
            CreateContractCommand(
                vendor_id="v1",
                company_id="comp1",
                contract_type="saas",
                title="SaaS License",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                annual_value=Decimal("12000.00"),
                currency="EUR",
                performed_by="user1",
            )
        )
        self.contract_repo.save.assert_called_once()
        saved = self.contract_repo.save.call_args[0][0]
        assert isinstance(saved, VendorContract)
        assert saved.title == "SaaS License"
        assert saved.status == ContractStatus.DRAFT

    def test_vendor_not_found(self):
        self.vendor_repo.find_by_id.return_value = None
        with pytest.raises(VendorNotFoundError):
            self.handler.handle(
                CreateContractCommand(
                    vendor_id="v1",
                    company_id="comp1",
                    contract_type="service",
                    title="Test",
                    start_date=date(2026, 1, 1),
                    performed_by="user1",
                )
            )
        self.contract_repo.save.assert_not_called()

    def test_empty_title_raises(self):
        self.vendor_repo.find_by_id.return_value = MagicMock()
        with pytest.raises(ValueError):
            self.handler.handle(
                CreateContractCommand(
                    vendor_id="v1",
                    company_id="comp1",
                    contract_type="service",
                    title="",
                    start_date=date(2026, 1, 1),
                    performed_by="user1",
                )
            )


class TestUpdateContractCommandHandler:
    def setup_method(self):
        self.contract_repo = MagicMock()
        self.handler = UpdateContractCommandHandler(
            contract_repo=self.contract_repo,
        )

    def _make_contract(self) -> VendorContract:
        return VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SERVICE,
            title="Original",
            start_date=date(2026, 1, 1),
        )

    def test_updates_contract(self):
        contract = self._make_contract()
        self.contract_repo.find_by_id.return_value = contract
        self.handler.handle(
            UpdateContractCommand(
                contract_id=contract.id,
                vendor_id="v1",
                company_id="comp1",
                title="Updated Title",
                annual_value=Decimal("5000.00"),
                performed_by="user1",
            )
        )
        self.contract_repo.save.assert_called_once()
        assert contract.title == "Updated Title"
        assert contract.annual_value == Decimal("5000.00")

    def test_not_found_raises(self):
        self.contract_repo.find_by_id.return_value = None
        with pytest.raises(ContractNotFoundError):
            self.handler.handle(
                UpdateContractCommand(
                    contract_id="c1",
                    vendor_id="v1",
                    company_id="comp1",
                    title="New",
                    performed_by="user1",
                )
            )


class TestChangeContractStatusCommandHandler:
    def setup_method(self):
        self.contract_repo = MagicMock()
        self.handler = ChangeContractStatusCommandHandler(
            contract_repo=self.contract_repo,
        )

    def test_valid_transition(self):
        contract = VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SERVICE,
            title="Test",
            start_date=date(2026, 1, 1),
        )
        self.contract_repo.find_by_id.return_value = contract
        self.handler.handle(
            ChangeContractStatusCommand(
                contract_id=contract.id,
                vendor_id="v1",
                company_id="comp1",
                new_status="active",
                performed_by="user1",
            )
        )
        assert contract.status == ContractStatus.ACTIVE
        self.contract_repo.save.assert_called_once()

    def test_invalid_transition_raises(self):
        contract = VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SERVICE,
            title="Test",
            start_date=date(2026, 1, 1),
        )
        self.contract_repo.find_by_id.return_value = contract
        with pytest.raises(InvalidContractTransitionError):
            self.handler.handle(
                ChangeContractStatusCommand(
                    contract_id=contract.id,
                    vendor_id="v1",
                    company_id="comp1",
                    new_status="expired",
                    performed_by="user1",
                )
            )

    def test_not_found_raises(self):
        self.contract_repo.find_by_id.return_value = None
        with pytest.raises(ContractNotFoundError):
            self.handler.handle(
                ChangeContractStatusCommand(
                    contract_id="c1",
                    vendor_id="v1",
                    company_id="comp1",
                    new_status="active",
                    performed_by="user1",
                )
            )


class TestSoftDeleteContractCommandHandler:
    def setup_method(self):
        self.contract_repo = MagicMock()
        self.handler = SoftDeleteContractCommandHandler(
            contract_repo=self.contract_repo,
        )

    def test_soft_deletes(self):
        contract = VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SERVICE,
            title="Test",
            start_date=date(2026, 1, 1),
        )
        self.contract_repo.find_by_id.return_value = contract
        self.handler.handle(
            SoftDeleteContractCommand(
                contract_id=contract.id,
                vendor_id="v1",
                company_id="comp1",
                performed_by="user1",
            )
        )
        self.contract_repo.soft_delete.assert_called_once()

    def test_not_found_raises(self):
        self.contract_repo.find_by_id.return_value = None
        with pytest.raises(ContractNotFoundError):
            self.handler.handle(
                SoftDeleteContractCommand(
                    contract_id="c1",
                    vendor_id="v1",
                    company_id="comp1",
                    performed_by="user1",
                )
            )
