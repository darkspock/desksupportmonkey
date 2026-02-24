from typing import Any
from urllib.parse import quote

from src.custom_field_bc.definition.domain.enums import FieldType
from src.custom_field_bc.definition.domain.repository import (
    CustomFieldDefinitionRepositoryInterface,
)


class CustomFieldEnrichmentService:
    def __init__(
        self, definition_repo: CustomFieldDefinitionRepositoryInterface
    ) -> None:
        self.definition_repo = definition_repo

    def enrich(
        self,
        company_id: str,
        entity_type: str,
        custom_fields_data: dict,
    ) -> list[dict[str, Any]]:
        definitions = self.definition_repo.find_by_entity_type(
            company_id, entity_type
        )
        return self._build_enriched(definitions, custom_fields_data)

    def enrich_batch(
        self,
        company_id: str,
        entity_type: str,
        entities_data: list[dict],
    ) -> list[list[dict[str, Any]]]:
        definitions = self.definition_repo.find_by_entity_type(
            company_id, entity_type
        )
        return [
            self._build_enriched(definitions, data)
            for data in entities_data
        ]

    @staticmethod
    def _build_enriched(
        definitions: list, custom_fields_data: dict
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for defn in sorted(definitions, key=lambda d: d.sort_order):
            entry: dict[str, Any] = {
                "key": defn.field_key,
                "label": defn.label,
                "type": defn.field_type,
                "value": custom_fields_data.get(defn.field_key),
                "required": defn.required,
                "is_active": defn.is_active,
                "visible_to_employees": defn.visible_to_employees,
            }
            if defn.field_type in (FieldType.SELECT, FieldType.MULTI_SELECT):
                entry["options"] = defn.options
            if defn.field_type == FieldType.FILE and isinstance(
                entry["value"], list
            ):
                entry["value"] = [
                    {
                        **f,
                        "download_path": (
                            f"/custom-fields/files/{f['id']}"
                            f"/download?key={quote(f['key'], safe='')}"
                        ),
                    }
                    for f in entry["value"]
                ]
            result.append(entry)
        return result
