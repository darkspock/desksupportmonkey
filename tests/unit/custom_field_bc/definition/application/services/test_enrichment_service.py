from unittest.mock import MagicMock

from src.custom_field_bc.definition.application.services.enrichment_service import (
    CustomFieldEnrichmentService,
)
from src.custom_field_bc.definition.domain.entities import CustomFieldDefinition


def _make_definition(
    field_key: str = "test_field",
    label: str = "Test Field",
    field_type: str = "text",
    sort_order: int = 0,
    is_active: bool = True,
    required: bool = False,
    visible_to_employees: bool = True,
    options: list | None = None,
) -> CustomFieldDefinition:
    return CustomFieldDefinition(
        id=f"def-{field_key}",
        company_id="comp-1",
        entity_type="asset",
        field_key=field_key,
        label=label,
        description=None,
        field_type=field_type,
        options=options,
        required=required,
        sort_order=sort_order,
        is_active=is_active,
        visible_to_employees=visible_to_employees,
    )


class TestEnrich:
    def _make_service(self, definitions: list[CustomFieldDefinition]):
        repo = MagicMock()
        repo.find_by_entity_type.return_value = definitions
        return CustomFieldEnrichmentService(repo)

    def test_returns_all_definitions_sorted_by_sort_order(self):
        svc = self._make_service([
            _make_definition(field_key="b", label="B", sort_order=2),
            _make_definition(field_key="a", label="A", sort_order=1),
            _make_definition(field_key="c", label="C", sort_order=0),
        ])
        result = svc.enrich("comp-1", "asset", {"a": "val_a", "b": "val_b", "c": "val_c"})
        assert len(result) == 3
        assert result[0]["key"] == "c"
        assert result[1]["key"] == "a"
        assert result[2]["key"] == "b"

    def test_includes_inactive_definitions(self):
        svc = self._make_service([
            _make_definition(field_key="active", is_active=True, sort_order=0),
            _make_definition(field_key="inactive", is_active=False, sort_order=1),
        ])
        result = svc.enrich("comp-1", "asset", {"active": "val"})
        assert len(result) == 2
        assert result[0]["is_active"] is True
        assert result[1]["is_active"] is False

    def test_missing_values_shown_as_null(self):
        svc = self._make_service([
            _make_definition(field_key="present", sort_order=0),
            _make_definition(field_key="missing", sort_order=1),
        ])
        result = svc.enrich("comp-1", "asset", {"present": "hello"})
        assert result[0]["value"] == "hello"
        assert result[1]["value"] is None

    def test_options_included_for_select(self):
        svc = self._make_service([
            _make_definition(
                field_key="color",
                field_type="select",
                options=["Red", "Blue"],
            ),
        ])
        result = svc.enrich("comp-1", "asset", {"color": "Red"})
        assert result[0]["options"] == ["Red", "Blue"]

    def test_options_included_for_multi_select(self):
        svc = self._make_service([
            _make_definition(
                field_key="tags",
                field_type="multi_select",
                options=["A", "B", "C"],
            ),
        ])
        result = svc.enrich("comp-1", "asset", {"tags": ["A", "C"]})
        assert result[0]["options"] == ["A", "B", "C"]
        assert result[0]["value"] == ["A", "C"]

    def test_no_options_for_text_field(self):
        svc = self._make_service([
            _make_definition(field_key="name", field_type="text"),
        ])
        result = svc.enrich("comp-1", "asset", {"name": "test"})
        assert "options" not in result[0]

    def test_enriched_entry_contains_all_metadata(self):
        svc = self._make_service([
            _make_definition(
                field_key="cost",
                label="Cost Center",
                field_type="text",
                required=True,
                visible_to_employees=False,
            ),
        ])
        result = svc.enrich("comp-1", "asset", {"cost": "IT-001"})
        entry = result[0]
        assert entry["key"] == "cost"
        assert entry["label"] == "Cost Center"
        assert entry["type"] == "text"
        assert entry["value"] == "IT-001"
        assert entry["required"] is True
        assert entry["is_active"] is True
        assert entry["visible_to_employees"] is False


class TestEnrichBatch:
    def _make_service(self, definitions: list[CustomFieldDefinition]):
        repo = MagicMock()
        repo.find_by_entity_type.return_value = definitions
        return CustomFieldEnrichmentService(repo)

    def test_batch_enrichment_one_query_for_n_entities(self):
        defns = [_make_definition(field_key="a", sort_order=0)]
        repo = MagicMock()
        repo.find_by_entity_type.return_value = defns
        svc = CustomFieldEnrichmentService(repo)

        entities_data = [{"a": "val1"}, {"a": "val2"}, {}]
        result = svc.enrich_batch("comp-1", "asset", entities_data)

        # Only 1 call to find_by_entity_type
        repo.find_by_entity_type.assert_called_once_with("comp-1", "asset")

        assert len(result) == 3
        assert result[0][0]["value"] == "val1"
        assert result[1][0]["value"] == "val2"
        assert result[2][0]["value"] is None

    def test_batch_empty_list(self):
        svc = self._make_service([_make_definition()])
        result = svc.enrich_batch("comp-1", "asset", [])
        assert result == []


class TestFileFieldEnrichment:
    def _make_service(self, definitions: list):
        repo = MagicMock()
        repo.find_by_entity_type.return_value = definitions
        return CustomFieldEnrichmentService(repo)

    def test_file_field_adds_download_path(self):
        svc = self._make_service([
            _make_definition(field_key="docs", field_type="file", sort_order=0),
        ])
        file_data = [
            {
                "id": "ulid1",
                "name": "report.pdf",
                "size": 102400,
                "mime": "application/pdf",
                "key": "cf-files/comp-1/asset/docs/ulid1.pdf",
            }
        ]
        result = svc.enrich("comp-1", "asset", {"docs": file_data})
        entry = result[0]
        assert entry["type"] == "file"
        assert len(entry["value"]) == 1
        enriched_file = entry["value"][0]
        assert "download_path" in enriched_file
        assert "/custom-fields/files/ulid1/download" in enriched_file["download_path"]
        assert "key=" in enriched_file["download_path"]

    def test_file_field_null_value_not_enriched(self):
        svc = self._make_service([
            _make_definition(field_key="docs", field_type="file", sort_order=0),
        ])
        result = svc.enrich("comp-1", "asset", {})
        assert result[0]["value"] is None

    def test_file_field_empty_list_enriched(self):
        svc = self._make_service([
            _make_definition(field_key="docs", field_type="file", sort_order=0),
        ])
        result = svc.enrich("comp-1", "asset", {"docs": []})
        assert result[0]["value"] == []
