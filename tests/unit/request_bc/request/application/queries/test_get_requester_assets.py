from unittest.mock import MagicMock

from src.request_bc.request.application.queries.get_requester_assets import (
    GetRequesterAssetsQuery,
    GetRequesterAssetsQueryHandler,
)


def _make_mock_request(
    created_by: str = "u1",
    affected_asset_ids: list[str] | None = None,
):
    req = MagicMock()
    req.id = "r1"
    req.company_id = "c1"
    req.created_by = created_by
    req.data = {}
    if affected_asset_ids:
        req.data["affected_asset_ids"] = affected_asset_ids
    return req


def _make_mock_asset(
    asset_id: str,
    brand: str = "Dell",
    model: str = "Latitude 5520",
    serial_number: str = "SN12345",
    asset_type: str = "laptop",
    criticality: str = "medium",
    status: str = "active",
):
    asset = MagicMock()
    asset.id = asset_id
    asset.brand = brand
    asset.model = model
    asset.serial_number = serial_number
    asset.type = asset_type
    asset.criticality = MagicMock()
    asset.criticality.value = criticality
    asset.status = MagicMock()
    asset.status.value = status
    return asset


class TestGetRequesterAssetsQuery:
    def setup_method(self):
        self.request_repo = MagicMock()
        self.asset_repo = MagicMock()
        self.handler = GetRequesterAssetsQueryHandler(
            request_repo=self.request_repo,
            asset_repo=self.asset_repo,
        )
        self.query = GetRequesterAssetsQuery(
            request_id="r1", company_id="c1",
        )

    def test_happy_path_returns_assets_with_is_affected(self):
        request = _make_mock_request(
            created_by="u1",
            affected_asset_ids=["a1"],
        )
        self.request_repo.find_by_id.return_value = request

        asset1 = _make_mock_asset("a1", brand="Dell", model="Lat 5520")
        asset2 = _make_mock_asset("a2", brand="HP", model="ProBook 450")
        self.asset_repo.find_by_assigned_to.return_value = [asset1, asset2]

        result = self.handler.handle(self.query)

        assert len(result) == 2

        dto_a1 = next(d for d in result if d.id == "a1")
        assert dto_a1.is_affected is True
        assert dto_a1.brand == "Dell"
        assert dto_a1.model == "Lat 5520"

        dto_a2 = next(d for d in result if d.id == "a2")
        assert dto_a2.is_affected is False
        assert dto_a2.brand == "HP"

        # Verified that find_by_assigned_to was called with requester
        self.asset_repo.find_by_assigned_to.assert_called_once_with("u1", "c1")

    def test_request_not_found_returns_empty(self):
        self.request_repo.find_by_id.return_value = None

        result = self.handler.handle(self.query)

        assert result == []
        self.asset_repo.find_by_assigned_to.assert_not_called()

    def test_no_assigned_assets_returns_empty(self):
        request = _make_mock_request(created_by="u1")
        self.request_repo.find_by_id.return_value = request
        self.asset_repo.find_by_assigned_to.return_value = []

        result = self.handler.handle(self.query)

        assert result == []

    def test_mixed_affected_and_non_affected(self):
        request = _make_mock_request(
            created_by="u1",
            affected_asset_ids=["a2", "a3"],
        )
        self.request_repo.find_by_id.return_value = request

        assets = [
            _make_mock_asset("a1"),
            _make_mock_asset("a2"),
            _make_mock_asset("a3"),
            _make_mock_asset("a4"),
        ]
        self.asset_repo.find_by_assigned_to.return_value = assets

        result = self.handler.handle(self.query)

        affected = {d.id for d in result if d.is_affected}
        not_affected = {d.id for d in result if not d.is_affected}

        assert affected == {"a2", "a3"}
        assert not_affected == {"a1", "a4"}

    def test_no_affected_asset_ids_in_data(self):
        """When request.data has no affected_asset_ids key, all assets are not affected."""
        request = _make_mock_request(created_by="u1")
        # data is {} with no affected_asset_ids
        self.request_repo.find_by_id.return_value = request

        self.asset_repo.find_by_assigned_to.return_value = [
            _make_mock_asset("a1"),
        ]

        result = self.handler.handle(self.query)

        assert len(result) == 1
        assert result[0].is_affected is False

    def test_dto_fields_populated_correctly(self):
        request = _make_mock_request(created_by="u1")
        self.request_repo.find_by_id.return_value = request

        asset = _make_mock_asset(
            asset_id="a1",
            brand="Lenovo",
            model="ThinkPad X1",
            serial_number="TH123",
            asset_type="laptop",
            criticality="high",
            status="active",
        )
        self.asset_repo.find_by_assigned_to.return_value = [asset]

        result = self.handler.handle(self.query)

        assert len(result) == 1
        dto = result[0]
        assert dto.id == "a1"
        assert dto.brand == "Lenovo"
        assert dto.model == "ThinkPad X1"
        assert dto.serial_number == "TH123"
        assert dto.type == "laptop"
        assert dto.criticality == "high"
        assert dto.status == "active"
        assert dto.is_affected is False

    def test_asset_with_none_criticality(self):
        """Assets without criticality set should return None for criticality."""
        request = _make_mock_request(created_by="u1")
        self.request_repo.find_by_id.return_value = request

        asset = _make_mock_asset("a1")
        asset.criticality = None
        self.asset_repo.find_by_assigned_to.return_value = [asset]

        result = self.handler.handle(self.query)

        assert len(result) == 1
        assert result[0].criticality is None
