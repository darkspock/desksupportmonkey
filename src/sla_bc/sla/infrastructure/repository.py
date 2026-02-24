from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func, select, text
from sqlalchemy.orm import Session

from src.sla_bc.sla.domain.entities import SlaBreachRecord, SlaPolicy
from src.sla_bc.sla.domain.enums import SlaBreachType
from src.sla_bc.sla.domain.repository import SlaRepositoryInterface
from src.sla_bc.sla.infrastructure.models import (
    SlaBreachRecordModel,
    SlaPolicyModel,
)


class SlaRepository(SlaRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    # ---- helpers ----

    def _policy_to_entity(self, m: SlaPolicyModel) -> SlaPolicy:
        return SlaPolicy(
            id=m.id,
            company_id=m.company_id,
            name=m.name,
            priority=m.priority,
            request_type=m.request_type,
            response_time_hours=m.response_time_hours,
            resolution_time_hours=m.resolution_time_hours,
            warning_threshold_pct=m.warning_threshold_pct,
            escalate_on_breach=m.escalate_on_breach,
            is_active=m.is_active,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def _breach_to_entity(self, m: SlaBreachRecordModel) -> SlaBreachRecord:
        return SlaBreachRecord(
            id=m.id,
            company_id=m.company_id,
            request_id=m.request_id,
            policy_id=m.policy_id,
            breach_type=SlaBreachType(m.breach_type),
            target_hours=m.target_hours,
            actual_hours=m.actual_hours,
            escalated=m.escalated,
            created_at=m.created_at,
        )

    # ---- Policies ----

    def save_policy(self, policy: SlaPolicy) -> None:
        existing = self.session.execute(
            select(SlaPolicyModel).where(SlaPolicyModel.id == policy.id)
        ).scalar_one_or_none()

        if existing:
            existing.name = policy.name
            existing.priority = policy.priority
            existing.request_type = policy.request_type
            existing.response_time_hours = policy.response_time_hours
            existing.resolution_time_hours = policy.resolution_time_hours
            existing.warning_threshold_pct = policy.warning_threshold_pct
            existing.escalate_on_breach = policy.escalate_on_breach
            existing.is_active = policy.is_active
            existing.updated_at = policy.updated_at
        else:
            model = SlaPolicyModel(
                id=policy.id,
                company_id=policy.company_id,
                name=policy.name,
                priority=policy.priority,
                request_type=policy.request_type,
                response_time_hours=policy.response_time_hours,
                resolution_time_hours=policy.resolution_time_hours,
                warning_threshold_pct=policy.warning_threshold_pct,
                escalate_on_breach=policy.escalate_on_breach,
                is_active=policy.is_active,
            )
            self.session.add(model)
        self.session.flush()

    def find_policy_by_id(
        self, policy_id: str, company_id: str
    ) -> Optional[SlaPolicy]:
        m = self.session.execute(
            select(SlaPolicyModel).where(
                SlaPolicyModel.id == policy_id,
                SlaPolicyModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._policy_to_entity(m) if m else None

    def find_policies(
        self, company_id: str, is_active: Optional[bool] = None
    ) -> list[SlaPolicy]:
        stmt = select(SlaPolicyModel).where(
            SlaPolicyModel.company_id == company_id
        )
        if is_active is not None:
            stmt = stmt.where(SlaPolicyModel.is_active == is_active)
        stmt = stmt.order_by(SlaPolicyModel.priority, SlaPolicyModel.request_type)
        rows = self.session.execute(stmt).scalars().all()
        return [self._policy_to_entity(r) for r in rows]

    def find_policy_for_request(
        self, company_id: str, priority: str, request_type: Optional[str] = None
    ) -> Optional[SlaPolicy]:
        # Try type-specific policy first
        if request_type:
            m = self.session.execute(
                select(SlaPolicyModel).where(
                    SlaPolicyModel.company_id == company_id,
                    SlaPolicyModel.priority == priority,
                    SlaPolicyModel.request_type == request_type,
                    SlaPolicyModel.is_active.is_(True),
                )
            ).scalar_one_or_none()
            if m:
                return self._policy_to_entity(m)

        # Fallback to priority-only default
        m = self.session.execute(
            select(SlaPolicyModel).where(
                SlaPolicyModel.company_id == company_id,
                SlaPolicyModel.priority == priority,
                SlaPolicyModel.request_type.is_(None),
                SlaPolicyModel.is_active.is_(True),
            )
        ).scalar_one_or_none()
        return self._policy_to_entity(m) if m else None

    def find_active_policy_by_scope(
        self,
        company_id: str,
        priority: str,
        request_type: Optional[str],
    ) -> Optional[SlaPolicy]:
        stmt = select(SlaPolicyModel).where(
            SlaPolicyModel.company_id == company_id,
            SlaPolicyModel.priority == priority,
            SlaPolicyModel.is_active.is_(True),
        )
        if request_type is None:
            stmt = stmt.where(SlaPolicyModel.request_type.is_(None))
        else:
            stmt = stmt.where(SlaPolicyModel.request_type == request_type)

        m = self.session.execute(stmt).scalar_one_or_none()
        return self._policy_to_entity(m) if m else None

    # ---- Breach Records ----

    def save_breach(self, breach: SlaBreachRecord) -> None:
        model = SlaBreachRecordModel(
            id=breach.id,
            company_id=breach.company_id,
            request_id=breach.request_id,
            policy_id=breach.policy_id,
            breach_type=breach.breach_type.value,
            target_hours=breach.target_hours,
            actual_hours=breach.actual_hours,
            escalated=breach.escalated,
        )
        self.session.add(model)
        self.session.flush()

    def find_breaches_for_request(
        self, request_id: str, company_id: str
    ) -> list[SlaBreachRecord]:
        rows = (
            self.session.execute(
                select(SlaBreachRecordModel)
                .where(
                    SlaBreachRecordModel.request_id == request_id,
                    SlaBreachRecordModel.company_id == company_id,
                )
                .order_by(SlaBreachRecordModel.created_at)
            )
            .scalars()
            .all()
        )
        return [self._breach_to_entity(r) for r in rows]

    def has_breach_of_type(self, request_id: str, breach_type: str) -> bool:
        count = self.session.execute(
            select(func.count())
            .select_from(SlaBreachRecordModel)
            .where(
                SlaBreachRecordModel.request_id == request_id,
                SlaBreachRecordModel.breach_type == breach_type,
            )
        ).scalar()
        return (count or 0) > 0

    def find_breaches(
        self,
        company_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SlaBreachRecord], int]:
        base = select(SlaBreachRecordModel).where(
            SlaBreachRecordModel.company_id == company_id
        )
        if from_date:
            base = base.where(SlaBreachRecordModel.created_at >= from_date)
        if to_date:
            base = base.where(SlaBreachRecordModel.created_at <= to_date)

        total = self.session.execute(
            select(func.count()).select_from(base.subquery())
        ).scalar() or 0

        rows = (
            self.session.execute(
                base.order_by(SlaBreachRecordModel.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
        return [self._breach_to_entity(r) for r in rows], total

    # ---- Dashboard / Stats ----

    def compliance_stats(
        self, company_id: str, from_date: datetime, to_date: datetime
    ) -> dict:
        # Count resolved requests in period
        total_resolved = self.session.execute(
            text(
                """
                SELECT COUNT(*) FROM service_requests
                WHERE company_id = :cid
                  AND resolved_at >= :from_date
                  AND resolved_at <= :to_date
                  AND status IN ('resolved', 'rejected')
                """
            ),
            {"cid": company_id, "from_date": from_date, "to_date": to_date},
        ).scalar() or 0

        # Count requests that had resolution breaches
        breached = self.session.execute(
            text(
                """
                SELECT COUNT(DISTINCT request_id)
                FROM sla_breach_records
                WHERE company_id = :cid
                  AND breach_type = 'resolution_breach'
                  AND created_at >= :from_date
                  AND created_at <= :to_date
                """
            ),
            {"cid": company_id, "from_date": from_date, "to_date": to_date},
        ).scalar() or 0

        met = total_resolved - breached if total_resolved > breached else 0
        pct = round((met / total_resolved) * 100, 1) if total_resolved > 0 else 100.0

        return {
            "total_resolved": total_resolved,
            "met": met,
            "breached": breached,
            "compliance_pct": pct,
        }

    def compliance_by_priority(
        self, company_id: str, from_date: datetime, to_date: datetime
    ) -> list[dict]:
        rows = self.session.execute(
            text(
                """
                SELECT
                    sr.priority,
                    COUNT(*) AS total,
                    COUNT(b.request_id) AS breached
                FROM service_requests sr
                LEFT JOIN (
                    SELECT DISTINCT request_id
                    FROM sla_breach_records
                    WHERE company_id = :cid
                      AND breach_type = 'resolution_breach'
                      AND created_at >= :from_date
                      AND created_at <= :to_date
                ) b ON b.request_id = sr.id
                WHERE sr.company_id = :cid
                  AND sr.resolved_at >= :from_date
                  AND sr.resolved_at <= :to_date
                  AND sr.status IN ('resolved', 'rejected')
                GROUP BY sr.priority
                ORDER BY sr.priority
                """
            ),
            {"cid": company_id, "from_date": from_date, "to_date": to_date},
        ).fetchall()

        return [
            {
                "priority": r[0],
                "total": r[1],
                "breached": r[2],
                "met": r[1] - r[2],
                "compliance_pct": round(
                    ((r[1] - r[2]) / r[1]) * 100, 1
                ) if r[1] > 0 else 100.0,
            }
            for r in rows
        ]

    def compliance_by_type(
        self, company_id: str, from_date: datetime, to_date: datetime
    ) -> list[dict]:
        rows = self.session.execute(
            text(
                """
                SELECT
                    sr.type,
                    COUNT(*) AS total,
                    COUNT(b.request_id) AS breached
                FROM service_requests sr
                LEFT JOIN (
                    SELECT DISTINCT request_id
                    FROM sla_breach_records
                    WHERE company_id = :cid
                      AND breach_type = 'resolution_breach'
                      AND created_at >= :from_date
                      AND created_at <= :to_date
                ) b ON b.request_id = sr.id
                WHERE sr.company_id = :cid
                  AND sr.resolved_at >= :from_date
                  AND sr.resolved_at <= :to_date
                  AND sr.status IN ('resolved', 'rejected')
                GROUP BY sr.type
                ORDER BY sr.type
                """
            ),
            {"cid": company_id, "from_date": from_date, "to_date": to_date},
        ).fetchall()

        return [
            {
                "type": r[0],
                "total": r[1],
                "breached": r[2],
                "met": r[1] - r[2],
                "compliance_pct": round(
                    ((r[1] - r[2]) / r[1]) * 100, 1
                ) if r[1] > 0 else 100.0,
            }
            for r in rows
        ]

    def breach_trend(
        self,
        company_id: str,
        from_date: datetime,
        to_date: datetime,
        bucket: str = "week",
    ) -> list[dict]:
        rows = self.session.execute(
            text(
                f"""
                SELECT
                    date_trunc(:bucket, created_at) AS period,
                    COUNT(*) AS breach_count
                FROM sla_breach_records
                WHERE company_id = :cid
                  AND breach_type IN ('response_breach', 'resolution_breach')
                  AND created_at >= :from_date
                  AND created_at <= :to_date
                GROUP BY period
                ORDER BY period
                """
            ),
            {
                "bucket": bucket,
                "cid": company_id,
                "from_date": from_date,
                "to_date": to_date,
            },
        ).fetchall()

        return [
            {"period": r[0].isoformat() if r[0] else None, "count": r[1]}
            for r in rows
        ]
