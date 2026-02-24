from unittest.mock import MagicMock

import pytest

from src.custom_field_bc.definition.application.services.validation_service import (
    CustomFieldValidationService,
)
from src.custom_field_bc.definition.domain.entities import CustomFieldDefinition


def _make_definition(
    field_key: str = "test_field",
    label: str = "Test Field",
    field_type: str = "text",
    required: bool = False,
    options: list | None = None,
) -> CustomFieldDefinition:
    return CustomFieldDefinition(
        id="def-1",
        company_id="comp-1",
        entity_type="asset",
        field_key=field_key,
        label=label,
        description=None,
        field_type=field_type,
        options=options,
        required=required,
        sort_order=0,
        is_active=True,
        visible_to_employees=True,
    )


class TestValidateForSave:
    def _make_service(self, definitions: list[CustomFieldDefinition]):
        repo = MagicMock()
        repo.find_active_by_entity_type.return_value = definitions
        return CustomFieldValidationService(repo)

    # --- Text field ---

    def test_text_valid_string(self):
        svc = self._make_service([_make_definition(field_type="text")])
        result = svc.validate_for_save("comp-1", "asset", {"test_field": "hello"})
        assert result == {"test_field": "hello"}

    def test_text_rejects_non_string(self):
        svc = self._make_service([_make_definition(field_type="text")])
        with pytest.raises(ValueError, match="expects a text value"):
            svc.validate_for_save("comp-1", "asset", {"test_field": 123})

    # --- Number field ---

    def test_number_valid_int(self):
        svc = self._make_service([_make_definition(field_type="number")])
        result = svc.validate_for_save("comp-1", "asset", {"test_field": 42})
        assert result == {"test_field": 42}

    def test_number_valid_float(self):
        svc = self._make_service([_make_definition(field_type="number")])
        result = svc.validate_for_save("comp-1", "asset", {"test_field": 3.14})
        assert result == {"test_field": 3.14}

    def test_number_rejects_string(self):
        svc = self._make_service([_make_definition(field_type="number")])
        with pytest.raises(ValueError, match="expects a number value"):
            svc.validate_for_save("comp-1", "asset", {"test_field": "not-a-number"})

    def test_number_rejects_bool(self):
        svc = self._make_service([_make_definition(field_type="number")])
        with pytest.raises(ValueError, match="expects a number value"):
            svc.validate_for_save("comp-1", "asset", {"test_field": True})

    # --- Date field ---

    def test_date_valid_iso(self):
        svc = self._make_service([_make_definition(field_type="date")])
        result = svc.validate_for_save("comp-1", "asset", {"test_field": "2026-02-24"})
        assert result == {"test_field": "2026-02-24"}

    def test_date_rejects_bad_format(self):
        svc = self._make_service([_make_definition(field_type="date")])
        with pytest.raises(ValueError, match="ISO 8601"):
            svc.validate_for_save("comp-1", "asset", {"test_field": "24/02/2026"})

    def test_date_rejects_non_string(self):
        svc = self._make_service([_make_definition(field_type="date")])
        with pytest.raises(ValueError, match="ISO 8601"):
            svc.validate_for_save("comp-1", "asset", {"test_field": 20260224})

    # --- Boolean field ---

    def test_boolean_valid_true(self):
        svc = self._make_service([_make_definition(field_type="boolean")])
        result = svc.validate_for_save("comp-1", "asset", {"test_field": True})
        assert result == {"test_field": True}

    def test_boolean_valid_false(self):
        svc = self._make_service([_make_definition(field_type="boolean")])
        result = svc.validate_for_save("comp-1", "asset", {"test_field": False})
        assert result == {"test_field": False}

    def test_boolean_rejects_string(self):
        svc = self._make_service([_make_definition(field_type="boolean")])
        with pytest.raises(ValueError, match="expects a boolean"):
            svc.validate_for_save("comp-1", "asset", {"test_field": "true"})

    # --- Select field ---

    def test_select_valid_option(self):
        svc = self._make_service([
            _make_definition(field_type="select", options=["A", "B", "C"])
        ])
        result = svc.validate_for_save("comp-1", "asset", {"test_field": "B"})
        assert result == {"test_field": "B"}

    def test_select_rejects_invalid_option(self):
        svc = self._make_service([
            _make_definition(field_type="select", options=["A", "B", "C"])
        ])
        with pytest.raises(ValueError, match="invalid option 'D'"):
            svc.validate_for_save("comp-1", "asset", {"test_field": "D"})

    # --- Multi-select field ---

    def test_multi_select_valid_array(self):
        svc = self._make_service([
            _make_definition(field_type="multi_select", options=["X", "Y", "Z"])
        ])
        result = svc.validate_for_save("comp-1", "asset", {"test_field": ["X", "Z"]})
        assert result == {"test_field": ["X", "Z"]}

    def test_multi_select_rejects_invalid_item(self):
        svc = self._make_service([
            _make_definition(field_type="multi_select", options=["X", "Y", "Z"])
        ])
        with pytest.raises(ValueError, match="invalid option 'W'"):
            svc.validate_for_save("comp-1", "asset", {"test_field": ["X", "W"]})

    def test_multi_select_rejects_non_list(self):
        svc = self._make_service([
            _make_definition(field_type="multi_select", options=["X", "Y"])
        ])
        with pytest.raises(ValueError, match="expects a list"):
            svc.validate_for_save("comp-1", "asset", {"test_field": "X"})

    # --- Required field ---

    def test_required_field_missing_raises(self):
        svc = self._make_service([
            _make_definition(field_type="text", required=True)
        ])
        with pytest.raises(ValueError, match="Required custom field"):
            svc.validate_for_save("comp-1", "asset", {})

    def test_required_field_present_passes(self):
        svc = self._make_service([
            _make_definition(field_type="text", required=True)
        ])
        result = svc.validate_for_save("comp-1", "asset", {"test_field": "value"})
        assert result == {"test_field": "value"}

    def test_required_field_null_raises(self):
        svc = self._make_service([
            _make_definition(field_type="text", required=True)
        ])
        with pytest.raises(ValueError, match="cannot be null"):
            svc.validate_for_save("comp-1", "asset", {"test_field": None})

    # --- Unknown keys ---

    def test_unknown_keys_stripped(self):
        svc = self._make_service([_make_definition(field_type="text")])
        result = svc.validate_for_save(
            "comp-1", "asset", {"test_field": "hello", "deleted_field": "ignored"}
        )
        assert result == {"test_field": "hello"}
        assert "deleted_field" not in result

    # --- Empty dict ---

    def test_empty_dict_no_required_fields(self):
        svc = self._make_service([
            _make_definition(field_type="text", required=False)
        ])
        result = svc.validate_for_save("comp-1", "asset", {})
        assert result == {}

    # --- Null value for optional field ---

    def test_null_value_for_optional_field(self):
        svc = self._make_service([
            _make_definition(field_type="text", required=False)
        ])
        result = svc.validate_for_save("comp-1", "asset", {"test_field": None})
        assert result == {"test_field": None}

    # --- File field ---

    def _valid_file_entry(self, **overrides) -> dict:
        base = {
            "id": "ulid1",
            "name": "report.pdf",
            "size": 102400,
            "mime": "application/pdf",
            "key": "cf-files/comp-1/asset/docs/ulid1.pdf",
        }
        base.update(overrides)
        return base

    def test_file_valid_array(self):
        svc = self._make_service([_make_definition(field_type="file")])
        files = [self._valid_file_entry()]
        result = svc.validate_for_save("comp-1", "asset", {"test_field": files})
        assert result == {"test_field": files}

    def test_file_empty_array_valid(self):
        svc = self._make_service([_make_definition(field_type="file")])
        result = svc.validate_for_save("comp-1", "asset", {"test_field": []})
        assert result == {"test_field": []}

    def test_file_rejects_non_list(self):
        svc = self._make_service([_make_definition(field_type="file")])
        with pytest.raises(ValueError, match="expects a list of file objects"):
            svc.validate_for_save("comp-1", "asset", {"test_field": "not-a-list"})

    def test_file_rejects_too_many(self):
        svc = self._make_service([_make_definition(field_type="file")])
        files = [self._valid_file_entry(id=f"id-{i}") for i in range(11)]
        with pytest.raises(ValueError, match="at most 10 files"):
            svc.validate_for_save("comp-1", "asset", {"test_field": files})

    def test_file_rejects_invalid_mime(self):
        svc = self._make_service([_make_definition(field_type="file")])
        files = [self._valid_file_entry(mime="application/exe")]
        with pytest.raises(ValueError, match="unsupported MIME type"):
            svc.validate_for_save("comp-1", "asset", {"test_field": files})

    def test_file_rejects_missing_keys(self):
        svc = self._make_service([_make_definition(field_type="file")])
        files = [{"id": "ulid1", "name": "report.pdf"}]  # missing size, mime, key
        with pytest.raises(ValueError, match="missing keys"):
            svc.validate_for_save("comp-1", "asset", {"test_field": files})

    def test_file_rejects_non_dict_entry(self):
        svc = self._make_service([_make_definition(field_type="file")])
        with pytest.raises(ValueError, match="must be an object"):
            svc.validate_for_save("comp-1", "asset", {"test_field": ["not-a-dict"]})
