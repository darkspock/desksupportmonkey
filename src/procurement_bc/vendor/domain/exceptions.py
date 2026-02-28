class VendorNotFoundError(Exception):
    pass


class DuplicateVendorNameError(Exception):
    pass


class ContractNotFoundError(Exception):
    pass


class InvalidContractTransitionError(Exception):
    pass


class ContractDocumentNotFoundError(Exception):
    pass


class AssessmentNotFoundError(Exception):
    pass


class InvalidAssessmentScoreError(Exception):
    pass


class DependencyNotFoundError(Exception):
    pass
