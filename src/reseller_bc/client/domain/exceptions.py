class CompanyAlreadyLinkedToResellerException(Exception):
    def __init__(self, company_id: str):
        self.company_id = company_id
        super().__init__(f"Company {company_id} is already linked to a reseller")


class DemoAccountLimitExceededException(Exception):
    def __init__(self, reseller_id: str, limit: int = 5):
        self.reseller_id = reseller_id
        super().__init__(f"Reseller {reseller_id} has reached the maximum of {limit} active demo accounts")
