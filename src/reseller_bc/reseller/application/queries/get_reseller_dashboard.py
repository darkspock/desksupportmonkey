from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.reseller_bc.client.domain.repository import ResellerClientRepositoryInterface
from src.reseller_bc.commission.domain.repository import ResellerCommissionRepositoryInterface
from src.reseller_bc.reseller.application.dtos import ResellerDashboardDto
from src.reseller_bc.payout.domain.repository import ResellerPayoutRepositoryInterface
from src.reseller_bc.reseller.domain.exceptions import ResellerNotFoundException
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class GetResellerDashboardQuery(Query):
    reseller_id: str


class GetResellerDashboardQueryHandler(QueryHandler[GetResellerDashboardQuery, ResellerDashboardDto]):
    def __init__(
        self,
        repo: ResellerRepositoryInterface,
        client_repo: ResellerClientRepositoryInterface,
        commission_repo: Optional[ResellerCommissionRepositoryInterface] = None,
        payout_repo: Optional[ResellerPayoutRepositoryInterface] = None,
    ):
        self.repo = repo
        self.client_repo = client_repo
        self.commission_repo = commission_repo
        self.payout_repo = payout_repo

    def handle(self, query: GetResellerDashboardQuery) -> ResellerDashboardDto:
        reseller = self.repo.get_by_id(query.reseller_id)
        if reseller is None:
            raise ResellerNotFoundException(query.reseller_id)

        client_count = self.client_repo.count_by_reseller_id(query.reseller_id)

        total_commissions_cents = 0
        available_balance_cents = 0
        if self.commission_repo:
            total_commissions_cents = self.commission_repo.sum_all_commissions_by_reseller_id(reseller.id)
            confirmed = self.commission_repo.sum_confirmed_by_reseller_id(reseller.id)
            paid = self.commission_repo.sum_paid_by_reseller_id(reseller.id)
            clawbacks = self.commission_repo.sum_clawbacks_by_reseller_id(reseller.id)
            available_balance_cents = confirmed - paid + clawbacks

        pending_payout_cents = 0
        if self.payout_repo:
            pending_payout_cents = self.payout_repo.sum_requested_and_approved_by_reseller_id(reseller.id)

        return ResellerDashboardDto(
            reseller_id=reseller.id,
            name=reseller.name,
            referral_code=reseller.referral_code,
            status=reseller.status.value,
            client_count=client_count,
            total_commissions_cents=total_commissions_cents,
            available_balance_cents=available_balance_cents,
            pending_payout_cents=pending_payout_cents,
        )
