class InvitationLimitExceededException(Exception):
    def __init__(self, reseller_id: str, limit: int = 20):
        self.reseller_id = reseller_id
        super().__init__(f"Reseller {reseller_id} has reached the maximum of {limit} pending invitations")


class InvitationAlreadyExistsException(Exception):
    def __init__(self, reseller_id: str, email: str):
        self.reseller_id = reseller_id
        self.email = email
        super().__init__(f"A pending invitation already exists for {email}")
