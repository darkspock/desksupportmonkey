from datetime import date
from typing import Any

from src.custom_field_bc.definition.domain.entities import (
    CustomFieldDefinition,
)
from src.custom_field_bc.definition.domain.enums import FieldType
from src.custom_field_bc.definition.domain.file_constants import (
    ALLOWED_MIME_TYPES,
    MAX_FILES_PER_FIELD,
)
from src.custom_field_bc.definition.domain.repository import (
    CustomFieldDefinitionRepositoryInterface,
)


class CustomFieldValidationService:
    def __init__(
        self, definition_repo: CustomFieldDefinitionRepositoryInterface
    ) -> None:
        self.definition_repo = definition_repo

    def validate_for_save(
        self, company_id: str, entity_type: str, data: dict
    ) -> dict:
        definitions = self.definition_repo.find_active_by_entity_type(
            company_id, entity_type
        )
        active_keys: dict[str, CustomFieldDefinition] = {
            d.field_key: d for d in definitions
        }
        cleaned: dict[str, Any] = {}

        for key, value in data.items():
            if key not in active_keys:
                continue
            defn = active_keys[key]
            cleaned[key] = self._validate_value(defn, value)

        for defn in definitions:
            if defn.required and defn.field_key not in cleaned:
                raise ValueError(
                    f"Required custom field '{defn.label}' is missing"
                )

        return cleaned

    def _validate_value(
        self, defn: CustomFieldDefinition, value: Any
    ) -> Any:
        if value is None:
            if defn.required:
                raise ValueError(
                    f"Required custom field '{defn.label}' cannot be null"
                )
            return None

        ft = defn.field_type

        if ft == FieldType.TEXT:
            if not isinstance(value, str):
                raise ValueError(
                    f"Field '{defn.label}' expects a text value"
                )
            return value

        if ft == FieldType.NUMBER:
            if isinstance(value, bool):
                raise ValueError(
                    f"Field '{defn.label}' expects a number value"
                )
            if isinstance(value, (int, float)):
                return value
            raise ValueError(
                f"Field '{defn.label}' expects a number value"
            )

        if ft == FieldType.DATE:
            if not isinstance(value, str):
                raise ValueError(
                    f"Field '{defn.label}' expects an ISO 8601 date string"
                )
            try:
                date.fromisoformat(value)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Field '{defn.label}' expects an ISO 8601 date string"
                )
            return value

        if ft == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                raise ValueError(
                    f"Field '{defn.label}' expects a boolean value"
                )
            return value

        if ft == FieldType.SELECT:
            if not isinstance(value, str):
                raise ValueError(
                    f"Field '{defn.label}' expects a string value"
                )
            if defn.options and value not in defn.options:
                raise ValueError(
                    f"Field '{defn.label}': invalid option '{value}'. "
                    f"Valid options: {defn.options}"
                )
            return value

        if ft == FieldType.MULTI_SELECT:
            if not isinstance(value, list):
                raise ValueError(
                    f"Field '{defn.label}' expects a list of values"
                )
            if defn.options:
                for item in value:
                    if item not in defn.options:
                        raise ValueError(
                            f"Field '{defn.label}': invalid option '{item}'. "
                            f"Valid options: {defn.options}"
                        )
            return value

        if ft == FieldType.FILE:
            return self._validate_file_value(defn, value)

        return value

    @staticmethod
    def _validate_file_value(
        defn: CustomFieldDefinition, value: Any
    ) -> list[dict]:
        if not isinstance(value, list):
            raise ValueError(
                f"Field '{defn.label}' expects a list of file objects"
            )
        if len(value) > MAX_FILES_PER_FIELD:
            raise ValueError(
                f"Field '{defn.label}' allows at most "
                f"{MAX_FILES_PER_FIELD} files"
            )
        required_keys = {"id", "name", "size", "mime", "key"}
        for item in value:
            if not isinstance(item, dict):
                raise ValueError(
                    f"Field '{defn.label}': each file entry must be an object"
                )
            missing = required_keys - item.keys()
            if missing:
                raise ValueError(
                    f"Field '{defn.label}': file entry missing keys: "
                    f"{', '.join(sorted(missing))}"
                )
            if item["mime"] not in ALLOWED_MIME_TYPES:
                raise ValueError(
                    f"Field '{defn.label}': unsupported MIME type "
                    f"'{item['mime']}'"
                )
        return value
