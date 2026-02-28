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
    def test_returns_counts_from_db(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            ("laptop", 20),
            ("monitor", 10),
        ]
        result = repo.count_by_type("comp1")
        assert result["laptop"] == 20
        assert result["monitor"] == 10
        assert result.get("keyboard", 0) == 0
        assert len(result) == 2

    def test_empty_returns_empty_dict(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo.count_by_type("comp1")
        assert result == {}


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


class TestFindAllByCompany:
    def test_returns_all_assets(self):
        repo, session = _make_repo()
        mock_model = MagicMock()
        mock_model.id = "a1"
        mock_model.company_id = "comp1"
        mock_model.type = "laptop"
        mock_model.brand = "Dell"
        mock_model.model = "Latitude"
        mock_model.serial_number = "SN001"
        mock_model.status = "in_stock"
        mock_model.assigned_to = None
        mock_model.department_id = None
        mock_model.purchase_date = None
        mock_model.warranty_expiration = None
        mock_model.notes = None
        mock_model.purchase_cost_cents = None
        mock_model.location_id = None
        mock_model.custom_fields_data = None
        mock_model.criticality = None
        mock_model.impact_score = None
        mock_model.rto_minutes = None
        mock_model.rpo_minutes = None
        mock_model.bia_justification = None
        mock_model.bia_reviewed_at = None
        mock_model.bia_reviewed_by = None
        mock_model.created_at = None
        mock_model.updated_at = None
        session.execute.return_value.scalars.return_value.all.return_value = [mock_model]

        result = repo.find_all_by_company("comp1")
        assert len(result) == 1
        assert result[0].id == "a1"

    def test_empty_returns_empty(self):
        repo, session = _make_repo()
        session.execute.return_value.scalars.return_value.all.return_value = []
        result = repo.find_all_by_company("comp1")
        assert result == []
