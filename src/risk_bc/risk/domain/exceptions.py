class RiskNotFoundError(Exception):
    def __init__(self, risk_id: str):
        super().__init__(f"Risk '{risk_id}' not found")
        self.risk_id = risk_id


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: str, target: str):
        super().__init__(f"Cannot transition from '{current}' to '{target}'")
        self.current = current
        self.target = target


class RiskClosedError(Exception):
    def __init__(self) -> None:
        super().__init__("Cannot modify a closed risk")


class InvalidScoreError(Exception):
    def __init__(self, field: str, value: int):
        super().__init__(f"{field} must be between 1 and 5, got {value}")
        self.field = field
        self.value = value


class MitigationNotFoundError(Exception):
    def __init__(self, mitigation_id: str):
        super().__init__(f"Mitigation plan '{mitigation_id}' not found")
        self.mitigation_id = mitigation_id


class LinkNotFoundError(Exception):
    def __init__(self, link_id: str):
        super().__init__(f"Risk link '{link_id}' not found")
        self.link_id = link_id


class DuplicateLinkError(Exception):
    def __init__(self, link_type: str, link_id: str):
        super().__init__(f"Risk already linked to {link_type} '{link_id}'")
        self.link_type = link_type
        self.link_id = link_id
