import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import ulid

from src.custom_field_bc.definition.domain.enums import FieldType
from src.custom_field_bc.definition.domain.exceptions import OptionsRequiredError


@dataclass
class CustomFieldDefinition:
    id: str
    company_id: str
    entity_type: str
    field_key: str
    label: str
    description: Optional[str]
    field_type: str
    options: Optional[list[str]]
    required: bool
    sort_order: int
    is_active: bool
    visible_to_employees: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        entity_type: str,
        label: str,
        field_type: str,
        description: Optional[str] = None,
        options: Optional[list[str]] = None,
        required: bool = False,
        sort_order: int = 0,
        visible_to_employees: bool = True,
    ) -> "CustomFieldDefinition":
        cls._validate_options(field_type, options)
        field_key = cls._slugify(label)

        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            entity_type=entity_type,
            field_key=field_key,
            label=label.strip(),
            description=description.strip() if description else None,
            field_type=field_type,
            options=options,
            required=required,
            sort_order=sort_order,
            is_active=True,
            visible_to_employees=visible_to_employees,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _slugify(label: str) -> str:
        slug = label.strip().lower()
        slug = re.sub(r"[^a-z0-9\s_]", "", slug)
        slug = re.sub(r"\s+", "_", slug)
        slug = re.sub(r"_+", "_", slug)
        slug = slug.strip("_")
        return slug[:50]

    @staticmethod
    def _validate_options(field_type: str, options: Optional[list[str]]) -> None:
        needs_options = field_type in (FieldType.SELECT, FieldType.MULTI_SELECT)
        if needs_options and (not options or len(options) == 0):
            raise OptionsRequiredError(field_type)
        if not needs_options and options:
            raise OptionsRequiredError(
                f"Options are not allowed for field type '{field_type}'"
            )

    def update(
        self,
        label: Optional[str] = None,
        description: Optional[str] = None,
        required: Optional[bool] = None,
        options: Optional[list[str]] = None,
        visible_to_employees: Optional[bool] = None,
    ) -> None:
        if label is not None:
            self.label = label.strip()
        if description is not None:
            self.description = description.strip() if description else None
        if required is not None:
            self.required = required
        if options is not None:
            self._validate_options(self.field_type, options)
            self.options = options
        if visible_to_employees is not None:
            self.visible_to_employees = visible_to_employees
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)
