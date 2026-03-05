from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.reseller_bc.client.domain.entities import ResellerClient


@dataclass
class ResellerClientDto:
    id: str
    reseller_id: str
    company_id: str
    company_name: str
    source: str
    is_demo: bool
    demo_expires_at: Optional[datetime]
    plan: str
    company_status: str
    created_at: Optional[datetime]

    @classmethod
    def from_entity_with_company(
        cls,
        client: ResellerClient,
        company_name: str,
        plan: str,
        company_status: str,
    ) -> "ResellerClientDto":
        return cls(
            id=client.id,
            reseller_id=client.reseller_id,
            company_id=client.company_id,
            company_name=company_name,
            source=client.source.value,
            is_demo=client.is_demo,
            demo_expires_at=client.demo_expires_at,
            plan=plan,
            company_status=company_status,
            created_at=client.created_at,
        )


@dataclass
class ResellerClientListDto:
    items: list[ResellerClientDto]
    total: int


@dataclass
class DemoAccountCreatedDto:
    client_id: str
    company_id: str
    company_name: str
    admin_email: str
    admin_password: str
