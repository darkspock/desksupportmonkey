from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.reseller_bc.commission.domain.repository import ResellerCommissionRepositoryInterface


@dataclass
class GetAvailableBalanceQuery(Query):
    reseller_id: str


class GetAvailableBalanceQueryHandler(QueryHandler[GetAvailableBalanceQuery, int]):
    def __init__(self, commission_repo: ResellerCommissionRepositoryInterface):
        self.commission_repo = commission_repo

    def handle(self, query: GetAvailableBalanceQuery) -> int:
        confirmed = self.commission_repo.sum_confirmed_by_reseller_id(query.reseller_id)
        paid = self.commission_repo.sum_paid_by_reseller_id(query.reseller_id)
        clawbacks = self.commission_repo.sum_clawbacks_by_reseller_id(query.reseller_id)
        return confirmed - paid + clawbacks
