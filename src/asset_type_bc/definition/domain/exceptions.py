class AssetTypeDefinitionNotFoundError(Exception):
    def __init__(self, definition_id: str) -> None:
        super().__init__(
            f"Asset type definition not found: {definition_id}"
        )
        self.definition_id = definition_id


class DuplicateAssetTypeCodeError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(
            f"An asset type with code '{code}' already exists"
        )
        self.code = code


class AssetTypeInUseError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(
            f"Cannot delete asset type '{code}': it is in use by existing assets"
        )
        self.code = code
