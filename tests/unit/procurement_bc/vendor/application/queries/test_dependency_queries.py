from datetime import datetime
from unittest.mock import MagicMock

from src.procurement_bc.vendor.application.queries.concentration_risk import (
    ConcentrationRiskQuery,
    ConcentrationRiskQueryHandler,
)
from src.procurement_bc.vendor.application.queries.list_dependencies import (
    ListDependenciesQuery,
    ListDependenciesQueryHandler,
)
from src.procurement_bc.vendor.domain.entities import Vendor, VendorDependency
from src.procurement_bc.vendor.domain.enums import BusinessFunction


def _make_dep(vendor_id="v1", is_critical=True, **kw):
    defaults = dict(
        id="d1",
        vendor_id=vendor_id,
        company_id="c1",
        service_description="Service",
        business_function=BusinessFunction.OTHER,
        is_critical=is_critical,
        created_at=datetime(2026, 2, 26),
    )
    defaults.update(kw)
    return VendorDependency(**defaults)


class TestListDependenciesQueryHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = ListDependenciesQueryHandler(
            dependency_repo=self.repo,
        )

    def test_returns_paginated_list(self):
        d1 = _make_dep(id="d1")
        d2 = _make_dep(id="d2")
        self.repo.find_all_by_vendor.return_value = ([d1, d2], 2)

        dtos, total = self.handler.handle(
            ListDependenciesQuery(
                vendor_id="v1", company_id="c1",
            )
        )

        assert total == 2
        assert len(dtos) == 2
        assert dtos[0].business_function == "other"

    def test_returns_empty(self):
        self.repo.find_all_by_vendor.return_value = ([], 0)

        dtos, total = self.handler.handle(
            ListDependenciesQuery(
                vendor_id="v1", company_id="c1",
            )
        )

        assert total == 0
        assert dtos == []


class TestConcentrationRiskQueryHandler:
    def setup_method(self):
        self.dependency_repo = MagicMock()
        self.vendor_repo = MagicMock()
        self.handler = ConcentrationRiskQueryHandler(
            dependency_repo=self.dependency_repo,
            vendor_repo=self.vendor_repo,
        )

    def _make_vendor(self, vendor_id, name):
        return Vendor(id=vendor_id, company_id="c1", name=name)

    def test_single_vendor_100_percent(self):
        deps = [
            _make_dep(id="d1", vendor_id="v1"),
            _make_dep(id="d2", vendor_id="v1"),
        ]
        self.dependency_repo.find_all_critical_by_company.return_value = deps
        self.vendor_repo.find_by_id.return_value = self._make_vendor("v1", "VendorA")

        items = self.handler.handle(
            ConcentrationRiskQuery(company_id="c1")
        )

        assert len(items) == 1
        assert items[0].vendor_id == "v1"
        assert items[0].percentage == 1.0
        assert items[0].is_above_threshold is True
        assert items[0].critical_count == 2
        assert items[0].total_critical == 2

    def test_two_vendors_50_50(self):
        deps = [
            _make_dep(id="d1", vendor_id="v1"),
            _make_dep(id="d2", vendor_id="v2"),
        ]
        self.dependency_repo.find_all_critical_by_company.return_value = deps
        self.vendor_repo.find_by_id.side_effect = lambda vid, cid: (
            self._make_vendor(vid, f"Vendor{vid}")
        )

        items = self.handler.handle(
            ConcentrationRiskQuery(company_id="c1")
        )

        assert len(items) == 2
        for item in items:
            assert item.percentage == 0.5
            assert item.is_above_threshold is True

    def test_three_vendors_below_threshold(self):
        # v1=2, v2=2, v3=1 → 40%, 40%, 20%
        deps = [
            _make_dep(id="d1", vendor_id="v1"),
            _make_dep(id="d2", vendor_id="v1"),
            _make_dep(id="d3", vendor_id="v2"),
            _make_dep(id="d4", vendor_id="v2"),
            _make_dep(id="d5", vendor_id="v3"),
        ]
        self.dependency_repo.find_all_critical_by_company.return_value = deps
        self.vendor_repo.find_by_id.side_effect = lambda vid, cid: (
            self._make_vendor(vid, f"Vendor{vid}")
        )

        items = self.handler.handle(
            ConcentrationRiskQuery(company_id="c1")
        )

        assert len(items) == 3
        by_vendor = {i.vendor_id: i for i in items}
        assert by_vendor["v1"].percentage == 0.4
        assert by_vendor["v1"].is_above_threshold is True
        assert by_vendor["v2"].percentage == 0.4
        assert by_vendor["v2"].is_above_threshold is True
        assert by_vendor["v3"].percentage == 0.2
        assert by_vendor["v3"].is_above_threshold is False

    def test_no_critical_deps_returns_empty(self):
        self.dependency_repo.find_all_critical_by_company.return_value = []

        items = self.handler.handle(
            ConcentrationRiskQuery(company_id="c1")
        )

        assert items == []
