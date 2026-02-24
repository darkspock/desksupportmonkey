class SlaPolicyNotFoundError(Exception):
    def __init__(self, policy_id: str) -> None:
        super().__init__(f"SLA policy not found: {policy_id}")


class DuplicateSlaPolicyError(Exception):
    def __init__(self, priority: str, request_type: str | None) -> None:
        scope = f"priority={priority}"
        if request_type:
            scope += f", type={request_type}"
        super().__init__(f"An active SLA policy already exists for {scope}")


class InvalidSlaTargetsError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Response time must be less than resolution time"
        )
