import pytest

from src.procurement_bc.vendor.domain.entities import VendorDependency
from src.procurement_bc.vendor.domain.enums import BusinessFunction


class TestVendorDependencyCreate:
    def test_creates_dependency(self):
        dep = VendorDependency.create(
            vendor_id="v1",
            company_id="c1",
            service_description="Cloud hosting",
            business_function=BusinessFunction.CLOUD_INFRASTRUCTURE,
            is_critical=True,
        )
        assert dep.vendor_id == "v1"
        assert dep.service_description == "Cloud hosting"
        assert dep.business_function == BusinessFunction.CLOUD_INFRASTRUCTURE
        assert dep.is_critical is True
        assert dep.is_deleted is False

    def test_strips_description(self):
        dep = VendorDependency.create(
            vendor_id="v1",
            company_id="c1",
            service_description="  Cloud hosting  ",
            business_function=BusinessFunction.OTHER,
        )
        assert dep.service_description == "Cloud hosting"

    def test_empty_description_raises(self):
        with pytest.raises(ValueError):
            VendorDependency.create(
                vendor_id="v1",
                company_id="c1",
                service_description="",
                business_function=BusinessFunction.OTHER,
            )

    def test_whitespace_description_raises(self):
        with pytest.raises(ValueError):
            VendorDependency.create(
                vendor_id="v1",
                company_id="c1",
                service_description="   ",
                business_function=BusinessFunction.OTHER,
            )


class TestVendorDependencyUpdate:
    def test_update_fields(self):
        dep = VendorDependency.create(
            vendor_id="v1",
            company_id="c1",
            service_description="Old service",
            business_function=BusinessFunction.OTHER,
            is_critical=False,
        )
        dep.update(
            service_description="New service",
            business_function=BusinessFunction.SECURITY,
            is_critical=True,
            notes="Updated",
        )
        assert dep.service_description == "New service"
        assert dep.business_function == BusinessFunction.SECURITY
        assert dep.is_critical is True
        assert dep.notes == "Updated"

    def test_update_none_keeps_current(self):
        dep = VendorDependency.create(
            vendor_id="v1",
            company_id="c1",
            service_description="Service",
            business_function=BusinessFunction.IT_OPERATIONS,
            is_critical=True,
        )
        dep.update()
        assert dep.service_description == "Service"
        assert dep.is_critical is True

    def test_update_empty_description_raises(self):
        dep = VendorDependency.create(
            vendor_id="v1",
            company_id="c1",
            service_description="Service",
            business_function=BusinessFunction.OTHER,
        )
        with pytest.raises(ValueError):
            dep.update(service_description="  ")


class TestVendorDependencySoftDelete:
    def test_soft_delete(self):
        dep = VendorDependency.create(
            vendor_id="v1",
            company_id="c1",
            service_description="Service",
            business_function=BusinessFunction.OTHER,
        )
        assert dep.is_deleted is False
        dep.soft_delete()
        assert dep.is_deleted is True
