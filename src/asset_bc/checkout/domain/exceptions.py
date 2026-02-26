class CheckoutNotFoundError(Exception):
    def __init__(self, identifier: str = ""):
        super().__init__(f"Checkout not found: {identifier}" if identifier else "Checkout not found")


class ActiveCheckoutExistsError(Exception):
    def __init__(self, asset_id: str = ""):
        super().__init__(
            f"Asset '{asset_id}' already has an active checkout" if asset_id else "Asset already has an active checkout"
        )


class NoActiveCheckoutError(Exception):
    def __init__(self, asset_id: str = ""):
        super().__init__(
            f"Asset '{asset_id}' has no active checkout" if asset_id else "Asset has no active checkout"
        )


class CheckoutAlreadyAcceptedError(Exception):
    def __init__(self) -> None:
        super().__init__("Checkout has already been accepted")


class CheckoutNotOpenError(Exception):
    def __init__(self) -> None:
        super().__init__("Checkout is not open")


class UnauthorizedAcceptError(Exception):
    def __init__(self) -> None:
        super().__init__("Only the assigned employee can accept this checkout")


class CannotUnassignWithOpenCheckoutError(Exception):
    def __init__(self, asset_id: str = ""):
        super().__init__(
            f"Cannot unassign asset '{asset_id}': has an open checkout"
            if asset_id
            else "Cannot unassign asset: has an open checkout"
        )


class InvalidCheckoutAssetStatusError(Exception):
    def __init__(self, status: str = ""):
        super().__init__(
            f"Asset must be IN_STOCK or ASSIGNED to checkout (current: {status})"
            if status
            else "Asset must be IN_STOCK or ASSIGNED to checkout"
        )


class AssetAssignedToOtherError(Exception):
    def __init__(self, asset_id: str = "", current_user: str = ""):
        super().__init__(
            f"Asset '{asset_id}' is assigned to another user '{current_user}'"
            if asset_id
            else "Asset is assigned to another user"
        )
