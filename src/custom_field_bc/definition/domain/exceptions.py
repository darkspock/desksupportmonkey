class FieldDefinitionNotFoundError(Exception):
    def __init__(self, definition_id: str) -> None:
        super().__init__(f"Custom field definition not found: {definition_id}")
        self.definition_id = definition_id


class DuplicateFieldKeyError(Exception):
    def __init__(self, field_key: str, entity_type: str) -> None:
        super().__init__(
            f"A custom field with key '{field_key}' already exists for {entity_type}"
        )
        self.field_key = field_key
        self.entity_type = entity_type


class MaxFieldsExceededError(Exception):
    def __init__(self, entity_type: str, max_fields: int = 20) -> None:
        super().__init__(
            f"Maximum of {max_fields} custom fields reached for {entity_type}"
        )
        self.entity_type = entity_type
        self.max_fields = max_fields


class InvalidFieldTypeError(Exception):
    def __init__(self, field_type: str) -> None:
        super().__init__(f"Invalid field type: {field_type}")
        self.field_type = field_type


class OptionsRequiredError(Exception):
    def __init__(self, field_type: str) -> None:
        super().__init__(
            f"Options are required for field type '{field_type}'"
        )
        self.field_type = field_type
