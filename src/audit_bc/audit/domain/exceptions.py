class ControlNotFoundError(Exception):
    pass


class ControlCodeExistsError(Exception):
    pass


class PredefinedControlError(Exception):
    pass


class AuditEntryNotFoundError(Exception):
    pass


class GdprRequestNotFoundError(Exception):
    pass


class InvalidGdprStatusTransitionError(Exception):
    pass


class CannotAnonymizeSuperAdminError(Exception):
    pass


class CannotAnonymizeSelfError(Exception):
    pass


class UserAlreadyAnonymizedError(Exception):
    pass


class TargetUserNotFoundError(Exception):
    pass


class InvalidRetentionPeriodError(Exception):
    pass


class EvidenceNotFoundError(Exception):
    pass


class InvalidComplianceStatusError(Exception):
    pass
