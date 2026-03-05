class InvalidPayoutAmountException(Exception):
    def __init__(self, amount: int):
        super().__init__(f"Payout amount must be positive, got: {amount}")


class InvalidPayoutTransitionException(Exception):
    def __init__(self, from_status: str, to_status: str):
        super().__init__(f"Cannot transition payout from '{from_status}' to '{to_status}'")


class InsufficientBalanceException(Exception):
    def __init__(self, balance: int, min_payout: int):
        super().__init__(f"Insufficient balance: {balance} cents (minimum: {min_payout} cents)")


class PayoutAlreadyPendingException(Exception):
    def __init__(self, reseller_id: str):
        super().__init__(f"Reseller {reseller_id} already has a pending/approved payout")


class PayoutNotFoundException(Exception):
    def __init__(self, payout_id: str):
        super().__init__(f"Payout not found: {payout_id}")
