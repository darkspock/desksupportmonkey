from unittest.mock import MagicMock

import pytest

from src.procurement_bc.vendor.application.commands.create_dependency import (
    CreateDependencyCommand,
    CreateDependencyCommandHandler,
)
from src.procurement_bc.vendor.application.commands.soft_delete_dependency import (
    SoftDeleteDependencyCommand,
    SoftDeleteDependencyCommandHandler,
)
from src.procurement_bc.vendor.application.commands.update_dependency import (
    UpdateDependencyCommand,
    UpdateDependencyCommandHandler,
)
from src.procurement_bc.vendor.domain.entities import Vendor, VendorDependency
from src.procurement_bc.vendor.domain.enums import BusinessFunction
from src.procurement_bc.vendor.domain.exceptions import (
    DependencyNotFoundError,
    VendorNotFoundError,
)


class TestCreateDependencyCommandHandler:
    def setup_method(self):
        self.vendor_repo = MagicMock()
        self.dependency_repo = MagicMock()
        self.handler = CreateDependencyCommandHandler(
            vendor_repo=self.vendor_repo,
            dependency_repo=self.dependency_repo,
        )

    def test_creates_dependency(self):
        self.vendor_repo.find_by_id.return_value = Vendor(
            id="v1", company_id="c1", name="Test",
        )
        self.handler.handle(
            CreateDependencyCommand(
                vendor_id="v1",
                company_id="c1",
                service_description="Cloud hosting",
                business_function="cloud_infrastructure",
                is_critical=True,
            )
        )
        self.dependency_repo.save.assert_called_once()
        saved = self.dependency_repo.save.call_args[0][0]
        assert saved.service_description == "Cloud hosting"
        assert saved.is_critical is True

    def test_raises_vendor_not_found(self):
        self.vendor_repo.find_by_id.return_value = None
        with pytest.raises(VendorNotFoundError):
            self.handler.handle(
                CreateDependencyCommand(
                    vendor_id="v1",
                    company_id="c1",
                    service_description="Service",
                    business_function="other",
                )
            )


class TestUpdateDependencyCommandHandler:
    def setup_method(self):
        self.dependency_repo = MagicMock()
        self.handler = UpdateDependencyCommandHandler(
            dependency_repo=self.dependency_repo,
        )

    def test_updates_dependency(self):
        dep = VendorDependency.create(
            id="d1", vendor_id="v1", company_id="c1",
            service_description="Old",
            business_function=BusinessFunction.OTHER,
        )
        self.dependency_repo.find_by_id.return_value = dep
        self.handler.handle(
            UpdateDependencyCommand(
                dependency_id="d1",
                vendor_id="v1",
                company_id="c1",
                service_description="New service",
                is_critical=True,
            )
        )
        self.dependency_repo.save.assert_called_once()
        assert dep.service_description == "New service"
        assert dep.is_critical is True

    def test_raises_not_found(self):
        self.dependency_repo.find_by_id.return_value = None
        with pytest.raises(DependencyNotFoundError):
            self.handler.handle(
                UpdateDependencyCommand(
                    dependency_id="d1",
                    vendor_id="v1",
                    company_id="c1",
                )
            )


class TestSoftDeleteDependencyCommandHandler:
    def setup_method(self):
        self.dependency_repo = MagicMock()
        self.handler = SoftDeleteDependencyCommandHandler(
            dependency_repo=self.dependency_repo,
        )

    def test_deletes_dependency(self):
        dep = VendorDependency.create(
            id="d1", vendor_id="v1", company_id="c1",
            service_description="Service",
            business_function=BusinessFunction.OTHER,
        )
        self.dependency_repo.find_by_id.return_value = dep
        self.handler.handle(
            SoftDeleteDependencyCommand(
                dependency_id="d1",
                vendor_id="v1",
                company_id="c1",
            )
        )
        self.dependency_repo.soft_delete.assert_called_once_with(
            "d1", "v1", "c1",
        )

    def test_raises_not_found(self):
        self.dependency_repo.find_by_id.return_value = None
        with pytest.raises(DependencyNotFoundError):
            self.handler.handle(
                SoftDeleteDependencyCommand(
                    dependency_id="d1",
                    vendor_id="v1",
                    company_id="c1",
                )
            )
