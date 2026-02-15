from datetime import date
from unittest.mock import MagicMock

from src.asset_bc.asset.infrastructure.repository import AssetRepository


def _make_repo():
    session = MagicMock()
    repo = AssetRepository(session)
    return repo, session


class TestCountByStatus:
    def test_returns_all_statuses_with_defaults(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            ("in_stock", 10),
            ("assigned", 5),
        ]
        result = repo.count_by_status("comp1")
        assert result["in_stock"] == 10
        assert result["assigned"] == 5
        assert result["in_repair"] == 0
        assert result["decommissioned"] == 0

    def test_empty_returns_all_zeros(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo.count_by_status("comp1")
        assert all(v == 0 for v in result.values())
        assert len(result) == 4


class TestCountByType:
    def test_returns_all_types_with_defaults(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            ("laptop", 20),
            ("monitor", 10),
        ]
        result = repo.count_by_type("comp1")
        assert result["laptop"] == 20
        assert result["monitor"] == 10
        assert result["keyboard"] == 0
        assert result["other"] == 0
        assert len(result) == 7


class TestFindExpiringWarranties:
    def test_returns_items_with_days_remaining(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            ("asset1", "Dell", "Latitude", "SN001", date(2026, 3, 1), "user1"),
        ]
        result = repo.find_expiring_warranties("comp1", 30)
        assert len(result) == 1
        assert result[0]["id"] == "asset1"
        assert result[0]["brand"] == "Dell"
        assert result[0]["warranty_expiration"] == date(2026, 3, 1)
        assert isinstance(result[0]["days_remaining"], int)

    def test_empty_returns_empty(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo.find_expiring_warranties("comp1", 30)
        assert result == []


class TestFindAgingAssets:
    def test_returns_items_with_age_years(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            ("asset1", "Dell", "Latitude", "SN001", date(2021, 1, 15), "user1"),
        ]
        result = repo.find_aging_assets("comp1", 3)
        assert len(result) == 1
        assert result[0]["id"] == "asset1"
        assert result[0]["purchase_date"] == date(2021, 1, 15)
        assert result[0]["age_years"] > 0

    def test_empty_returns_empty(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo.find_aging_assets("comp1", 3)
        assert result == []
