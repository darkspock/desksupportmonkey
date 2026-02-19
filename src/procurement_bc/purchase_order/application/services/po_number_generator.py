from src.procurement_bc.purchase_order.domain.repository import (
    PurchaseOrderRepositoryInterface,
)


class PONumberGenerator:
    def __init__(
        self,
        po_repo: PurchaseOrderRepositoryInterface,
    ):
        self.po_repo = po_repo

    def generate(
        self,
        company_id: str,
        prefix: str,
        year: int,
    ) -> str:
        next_seq = self.po_repo.get_next_number(
            company_id, year,
        )
        return f"{prefix}-{year}-{next_seq:03d}"
