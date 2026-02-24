class IncidentNotFoundError(Exception):
    def __init__(self, incident_id: str):
        super().__init__(f"Security incident '{incident_id}' not found")
        self.incident_id = incident_id


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: str, target: str):
        super().__init__(
            f"Cannot transition from '{current}' to '{target}'"
        )
        self.current = current
        self.target = target


class CloseReasonRequiredError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "A close reason is required when closing an incident from an active state "
            "(not recovered)"
        )


class IncidentClosedError(Exception):
    def __init__(self) -> None:
        super().__init__("Cannot modify a closed incident")


class ReportNotFoundError(Exception):
    def __init__(self, report_id: str):
        super().__init__(f"Regulatory report '{report_id}' not found")
        self.report_id = report_id


class ReportNotGeneratedError(Exception):
    def __init__(self, report_id: str):
        super().__init__(
            f"Report '{report_id}' has not been generated yet"
        )
        self.report_id = report_id


class PostMortemAlreadyExistsError(Exception):
    def __init__(self, incident_id: str):
        super().__init__(
            f"A post-mortem already exists for incident '{incident_id}'"
        )


class PostMortemNotFoundError(Exception):
    def __init__(self, incident_id: str):
        super().__init__(
            f"No post-mortem found for incident '{incident_id}'"
        )


class IncidentNotClosableForPostMortemError(Exception):
    def __init__(self, status: str):
        super().__init__(
            f"Post-mortem can only be created for recovered or closed incidents, "
            f"current status is '{status}'"
        )


class AssetAlreadyLinkedError(Exception):
    def __init__(self, asset_id: str):
        super().__init__(f"Asset '{asset_id}' is already linked to this incident")


class AssetNotLinkedError(Exception):
    def __init__(self, asset_id: str):
        super().__init__(f"Asset '{asset_id}' is not linked to this incident")


class VendorAlreadyLinkedError(Exception):
    def __init__(self, vendor_id: str):
        super().__init__(f"Vendor '{vendor_id}' is already linked to this incident")


class VendorNotLinkedError(Exception):
    def __init__(self, vendor_id: str):
        super().__init__(f"Vendor '{vendor_id}' is not linked to this incident")
