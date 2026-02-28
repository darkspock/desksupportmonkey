class ChangeNotFoundError(Exception):
    def __init__(self, change_id: str):
        super().__init__(f"Change request '{change_id}' not found")
        self.change_id = change_id


class ChangeNotEditableError(Exception):
    def __init__(self, status: str):
        super().__init__(
            f"Change request cannot be edited in '{status}' status"
        )
        self.status = status


class RollbackPlanRequiredError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "A rollback plan is required for normal and emergency changes"
        )


class RejectionReasonRequiredError(Exception):
    def __init__(self) -> None:
        super().__init__("A reason is required when rejecting a change request")


class RollbackReasonRequiredError(Exception):
    def __init__(self) -> None:
        super().__init__("A reason is required when rolling back a change")


class UnauthorizedApprovalError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Only admin or super_admin can approve or reject change requests"
        )


class AssetAlreadyLinkedError(Exception): ...


class AssetNotLinkedError(Exception): ...


class ChangeNotUnlinkableError(Exception):
    """Unlinking only allowed in DRAFT, PENDING_APPROVAL, SCHEDULED."""

    def __init__(self, status: str):
        super().__init__(
            f"Cannot unlink assets in '{status}' status. "
            "Only allowed in draft, pending_approval, scheduled"
        )
        self.status = status


class PIRAlreadyExistsError(Exception):
    def __init__(self, change_id: str):
        super().__init__(
            f"A post-implementation review already exists for change '{change_id}'"
        )
        self.change_id = change_id


class PIRRequiredForEmergencyCloseError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Emergency changes require a post-implementation review before closing"
        )
