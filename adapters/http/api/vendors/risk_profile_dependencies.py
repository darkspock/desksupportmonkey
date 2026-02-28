from typing import Optional

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from src.incident_bc.incident.infrastructure.models import (
    IncidentVendorModel,
    SecurityIncidentModel,
)
from src.procurement_bc.vendor.application.ports import (
    IncidentByVendorReader,
    IncidentSummary,
    RiskByVendorReader,
    RiskSummary,
)
from src.risk_bc.risk.infrastructure.models import RiskLinkModel, RiskModel


class SqlIncidentByVendorReader(IncidentByVendorReader):
    """Implements IncidentByVendorReader using incident_bc models."""

    def __init__(self, session: Session):
        self.session = session

    def find_by_vendor(
        self,
        vendor_id: str,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[IncidentSummary], int]:
        from sqlalchemy import func

        stmt = (
            select(SecurityIncidentModel)
            .join(
                IncidentVendorModel,
                IncidentVendorModel.incident_id == SecurityIncidentModel.id,
            )
            .where(
                IncidentVendorModel.vendor_id == vendor_id,
                SecurityIncidentModel.company_id == company_id,
            )
        )

        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar() or 0

        models = (
            self.session.execute(
                stmt.order_by(SecurityIncidentModel.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )

        items = [
            IncidentSummary(
                id=m.id,
                title=m.title,
                severity=m.severity,
                status=m.status,
                created_at=m.created_at,
            )
            for m in models
        ]
        return items, total


class SqlRiskByVendorReader(RiskByVendorReader):
    """Implements RiskByVendorReader using risk_bc models."""

    def __init__(self, session: Session):
        self.session = session

    def find_by_vendor(
        self,
        vendor_id: str,
        company_id: str,
    ) -> list[RiskSummary]:
        models = (
            self.session.execute(
                select(RiskModel)
                .join(
                    RiskLinkModel,
                    RiskLinkModel.risk_id == RiskModel.id,
                )
                .where(
                    RiskLinkModel.link_type == "vendor",
                    RiskLinkModel.link_id == vendor_id,
                    RiskModel.company_id == company_id,
                )
                .order_by(RiskModel.created_at.desc())
            )
            .scalars()
            .all()
        )

        return [
            RiskSummary(
                id=m.id,
                title=m.title,
                risk_level=m.risk_level,
                status=m.status,
            )
            for m in models
        ]


def get_incident_reader(
    db: Session = Depends(get_db),
) -> SqlIncidentByVendorReader:
    return SqlIncidentByVendorReader(db)


def get_risk_reader(
    db: Session = Depends(get_db),
) -> SqlRiskByVendorReader:
    return SqlRiskByVendorReader(db)
