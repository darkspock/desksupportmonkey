from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.reseller_bc.payout.application.dtos import PayoutDto, PayoutListDto
from src.reseller_bc.payout.domain.repository import ResellerPayoutRepositoryInterface
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class ListPayoutsQuery(Query):
    reseller_id: Optional[str] = None
    offset: int = 0
    limit: int = 50


class ListPayoutsQueryHandler(QueryHandler[ListPayoutsQuery, PayoutListDto]):
    def __init__(
        self,
        payout_repo: ResellerPayoutRepositoryInterface,
        reseller_repo: ResellerRepositoryInterface,
    ):
        self.payout_repo = payout_repo
        self.reseller_repo = reseller_repo

    def handle(self, query: ListPayoutsQuery) -> PayoutListDto:
        if query.reseller_id:
            payouts = self.payout_repo.find_by_reseller_id(
                query.reseller_id, query.offset, query.limit
            )
            total = self.payout_repo.count_by_reseller_id(query.reseller_id)
        else:
            payouts = self.payout_repo.find_all(query.offset, query.limit)
            total = self.payout_repo.count_all()

        # Batch-load reseller names
        reseller_ids = list({p.reseller_id for p in payouts})
        resellers = {}
        for rid in reseller_ids:
            r = self.reseller_repo.get_by_id(rid)
            if r:
                resellers[rid] = r

        items = [
            PayoutDto(
                id=p.id,
                reseller_id=p.reseller_id,
                reseller_name=resellers[p.reseller_id].name if p.reseller_id in resellers else "Unknown",
                amount_cents=p.amount_cents,
                status=p.status.value,
                requested_at=p.requested_at,
                processed_at=p.processed_at,
                processed_by=p.processed_by,
                payment_reference=p.payment_reference,
                notes=p.notes,
            )
            for p in payouts
        ]
        return PayoutListDto(items=items, total=total)
