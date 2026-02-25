class ChecklistItemNotFoundError(Exception):
    def __init__(self, item_id: str) -> None:
        super().__init__(f"Checklist item not found: {item_id}")
        self.item_id = item_id


class IncompleteChecklistError(Exception):
    def __init__(self, request_id: str, remaining: int) -> None:
        super().__init__(
            f"Request '{request_id}' has {remaining} required checklist items incomplete"
        )
        self.request_id = request_id
        self.remaining = remaining
