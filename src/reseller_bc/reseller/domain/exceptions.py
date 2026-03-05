class ResellerNotFoundException(Exception):
    def __init__(self, identifier: str = ""):
        msg = f"Reseller not found: {identifier}" if identifier else "Reseller not found"
        super().__init__(msg)


class ResellerNotRegisteredException(Exception):
    def __init__(self, email: str = ""):
        msg = f"Not registered as a reseller: {email}" if email else "Not registered as a reseller"
        super().__init__(msg)


class ResellerDeactivatedException(Exception):
    def __init__(self, reseller_id: str = ""):
        msg = f"Reseller account is deactivated: {reseller_id}" if reseller_id else "Reseller account is deactivated"
        super().__init__(msg)


class ResellerSuspendedException(Exception):
    def __init__(self, reseller_id: str = ""):
        msg = f"Reseller account is suspended: {reseller_id}" if reseller_id else "Reseller account is suspended"
        super().__init__(msg)


class ResellerAlreadyExistsException(Exception):
    def __init__(self, email: str = ""):
        msg = f"A reseller with this email already exists: {email}" if email else "A reseller with this email already exists"
        super().__init__(msg)


class InvalidCommissionRateException(Exception):
    def __init__(self, rate: int | None = None):
        msg = f"Commission rate must be between 0 and 100, got: {rate}" if rate is not None else "Invalid commission rate"
        super().__init__(msg)


class InvalidMinPayoutException(Exception):
    def __init__(self, amount: int | None = None):
        msg = f"Minimum payout must be greater than 0, got: {amount}" if amount is not None else "Invalid minimum payout amount"
        super().__init__(msg)


class ReferralCodeCollisionException(Exception):
    def __init__(self) -> None:
        super().__init__("Failed to generate a unique referral code after multiple attempts")


class ResellerPendingApprovalException(Exception):
    def __init__(self, message: str = ""):
        msg = message if message else "Reseller account is pending approval"
        super().__init__(msg)


class ResellerInvalidPasswordException(Exception):
    def __init__(self, message: str = ""):
        msg = message if message else "Invalid password"
        super().__init__(msg)


class ResellerInvalidResetTokenException(Exception):
    def __init__(self, message: str = ""):
        msg = message if message else "Invalid or expired reset token"
        super().__init__(msg)


class ResellerOAuthProviderAlreadyLinkedError(Exception):
    def __init__(self, provider: str = ""):
        msg = f"OAuth provider already linked to a different account: {provider}" if provider else "OAuth provider already linked to a different account"
        super().__init__(msg)
