from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.risk_bc.risk.domain.entities import (
    MitigationPlan,
    Risk,
    RiskHistory,
    RiskLink,
)
from src.risk_bc.risk.domain.enums import (
    MitigationStatus,
    RiskCategory,
    RiskHistoryEventType,
    RiskLevel,
    RiskLinkType,
    RiskStatus,
    RiskTreatment,
    ReviewCadence,
)
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface
from src.risk_bc.risk.infrastructure.models import (
    MitigationPlanModel,
    RiskHistoryModel,
    RiskLinkModel,
    RiskModel,
)


class RiskRepository(RiskRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    # --- Risk ---

    def save(self, risk: Risk) -> None:
        existing = self.session.execute(
            select(RiskModel).where(RiskModel.id == risk.id)
        ).scalar_one_or_none()

        if existing:
            existing.company_id = risk.company_id
            existing.title = risk.title
            existing.description = risk.description
            existing.category = risk.category.value
            existing.status = risk.status.value
            existing.likelihood = risk.likelihood
            existing.impact = risk.impact
            existing.risk_level = risk.risk_level.value if risk.risk_level else None
            existing.treatment = risk.treatment.value if risk.treatment else None
            existing.review_cadence = (
                risk.review_cadence.value if risk.review_cadence else None
            )
            existing.next_review_at = risk.next_review_at
            existing.owner_id = risk.owner_id
            existing.created_by = risk.created_by
        else:
            model = RiskModel(
                id=risk.id,
                company_id=risk.company_id,
                title=risk.title,
                description=risk.description,
                category=risk.category.value,
                status=risk.status.value,
                likelihood=risk.likelihood,
                impact=risk.impact,
                risk_level=risk.risk_level.value if risk.risk_level else None,
                treatment=risk.treatment.value if risk.treatment else None,
                review_cadence=(
                    risk.review_cadence.value if risk.review_cadence else None
                ),
                next_review_at=risk.next_review_at,
                owner_id=risk.owner_id,
                created_by=risk.created_by,
            )
            self.session.add(model)
        self.session.flush()

    def find_by_id(self, risk_id: str, company_id: str) -> Optional[Risk]:
        model = self.session.execute(
            select(RiskModel).where(
                RiskModel.id == risk_id,
                RiskModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    def find_all(
        self, company_id: str, filters: dict
    ) -> tuple[list[Risk], int]:
        query = select(RiskModel).where(RiskModel.company_id == company_id)

        if filters.get("category"):
            query = query.where(RiskModel.category == filters["category"])
        if filters.get("status"):
            query = query.where(RiskModel.status == filters["status"])
        if filters.get("risk_level"):
            query = query.where(RiskModel.risk_level == filters["risk_level"])
        if filters.get("treatment"):
            query = query.where(RiskModel.treatment == filters["treatment"])
        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            query = query.where(RiskModel.title.ilike(search_term))

        count_query = select(func.count()).select_from(query.subquery())
        total = self.session.execute(count_query).scalar() or 0

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        offset = (page - 1) * page_size
        query = query.order_by(RiskModel.created_at.desc())
        query = query.offset(offset).limit(page_size)

        models = self.session.execute(query).scalars().all()
        return [self._to_entity(m) for m in models], total

    def delete(self, risk_id: str, company_id: str) -> None:
        self.session.execute(
            delete(RiskHistoryModel).where(
                RiskHistoryModel.risk_id == risk_id
            )
        )
        self.session.execute(
            delete(RiskLinkModel).where(
                RiskLinkModel.risk_id == risk_id
            )
        )
        self.session.execute(
            delete(MitigationPlanModel).where(
                MitigationPlanModel.risk_id == risk_id
            )
        )
        self.session.execute(
            delete(RiskModel).where(
                RiskModel.id == risk_id,
                RiskModel.company_id == company_id,
            )
        )
        self.session.flush()

    # --- History ---

    def add_history(self, entry: RiskHistory) -> None:
        model = RiskHistoryModel(
            id=entry.id,
            risk_id=entry.risk_id,
            event_type=entry.event_type.value,
            description=entry.description,
            actor_id=entry.actor_id,
            metadata_json=entry.metadata,
        )
        self.session.add(model)
        self.session.flush()

    def get_history(self, risk_id: str) -> list[RiskHistory]:
        models = (
            self.session.execute(
                select(RiskHistoryModel)
                .where(RiskHistoryModel.risk_id == risk_id)
                .order_by(RiskHistoryModel.created_at.desc())
            )
            .scalars()
            .all()
        )
        return [
            RiskHistory(
                id=m.id,
                risk_id=m.risk_id,
                event_type=RiskHistoryEventType(m.event_type),
                description=m.description,
                actor_id=m.actor_id,
                metadata=m.metadata_json,
                created_at=m.created_at,
            )
            for m in models
        ]

    # --- Mitigations ---

    def save_mitigation(self, plan: MitigationPlan) -> None:
        existing = self.session.execute(
            select(MitigationPlanModel).where(
                MitigationPlanModel.id == plan.id
            )
        ).scalar_one_or_none()

        if existing:
            existing.description = plan.description
            existing.status = plan.status.value
            existing.owner_id = plan.owner_id
            existing.target_date = plan.target_date
        else:
            model = MitigationPlanModel(
                id=plan.id,
                risk_id=plan.risk_id,
                description=plan.description,
                status=plan.status.value,
                owner_id=plan.owner_id,
                target_date=plan.target_date,
            )
            self.session.add(model)
        self.session.flush()

    def find_mitigation_by_id(
        self, mitigation_id: str, risk_id: str
    ) -> Optional[MitigationPlan]:
        model = self.session.execute(
            select(MitigationPlanModel).where(
                MitigationPlanModel.id == mitigation_id,
                MitigationPlanModel.risk_id == risk_id,
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_mitigation(model)

    def get_mitigations(self, risk_id: str) -> list[MitigationPlan]:
        models = (
            self.session.execute(
                select(MitigationPlanModel)
                .where(MitigationPlanModel.risk_id == risk_id)
                .order_by(MitigationPlanModel.created_at.desc())
            )
            .scalars()
            .all()
        )
        return [self._to_mitigation(m) for m in models]

    def delete_mitigation(self, mitigation_id: str, risk_id: str) -> None:
        self.session.execute(
            delete(MitigationPlanModel).where(
                MitigationPlanModel.id == mitigation_id,
                MitigationPlanModel.risk_id == risk_id,
            )
        )
        self.session.flush()

    # --- Links ---

    def add_link(self, link: RiskLink) -> None:
        model = RiskLinkModel(
            id=link.id,
            risk_id=link.risk_id,
            link_type=link.link_type.value,
            link_id=link.link_id,
        )
        self.session.add(model)
        self.session.flush()

    def get_links(self, risk_id: str) -> list[RiskLink]:
        models = (
            self.session.execute(
                select(RiskLinkModel)
                .where(RiskLinkModel.risk_id == risk_id)
                .order_by(RiskLinkModel.created_at.desc())
            )
            .scalars()
            .all()
        )
        return [
            RiskLink(
                id=m.id,
                risk_id=m.risk_id,
                link_type=RiskLinkType(m.link_type),
                link_id=m.link_id,
                created_at=m.created_at,
            )
            for m in models
        ]

    def delete_link(self, link_id: str, risk_id: str) -> None:
        self.session.execute(
            delete(RiskLinkModel).where(
                RiskLinkModel.id == link_id,
                RiskLinkModel.risk_id == risk_id,
            )
        )
        self.session.flush()

    # --- Dashboard ---

    def get_dashboard_stats(self, company_id: str) -> dict:
        base = select(RiskModel).where(RiskModel.company_id == company_id)

        total = self.session.execute(
            select(func.count()).select_from(base.subquery())
        ).scalar() or 0

        open_count = self.session.execute(
            select(func.count()).select_from(
                base.where(
                    RiskModel.status.in_(
                        [RiskStatus.OPEN.value, RiskStatus.UNDER_REVIEW.value]
                    )
                ).subquery()
            )
        ).scalar() or 0

        mitigated_count = self.session.execute(
            select(func.count()).select_from(
                base.where(
                    RiskModel.status == RiskStatus.MITIGATED.value
                ).subquery()
            )
        ).scalar() or 0

        accepted_count = self.session.execute(
            select(func.count()).select_from(
                base.where(
                    RiskModel.status == RiskStatus.ACCEPTED.value
                ).subquery()
            )
        ).scalar() or 0

        # By level
        level_rows = self.session.execute(
            select(RiskModel.risk_level, func.count())
            .where(
                RiskModel.company_id == company_id,
                RiskModel.risk_level.isnot(None),
            )
            .group_by(RiskModel.risk_level)
        ).all()
        by_level = {row[0]: row[1] for row in level_rows}

        # By category
        cat_rows = self.session.execute(
            select(RiskModel.category, func.count())
            .where(RiskModel.company_id == company_id)
            .group_by(RiskModel.category)
        ).all()
        by_category = {row[0]: row[1] for row in cat_rows}

        # Heat map data
        heat_rows = self.session.execute(
            select(
                RiskModel.likelihood,
                RiskModel.impact,
                func.count(),
            )
            .where(
                RiskModel.company_id == company_id,
                RiskModel.likelihood.isnot(None),
                RiskModel.impact.isnot(None),
            )
            .group_by(RiskModel.likelihood, RiskModel.impact)
        ).all()
        heat_map = [
            {"likelihood": row[0], "impact": row[1], "count": row[2]}
            for row in heat_rows
        ]

        # Overdue reviews
        now = datetime.now(timezone.utc)
        overdue_count = self.session.execute(
            select(func.count()).select_from(
                select(RiskModel)
                .where(
                    RiskModel.company_id == company_id,
                    RiskModel.next_review_at.isnot(None),
                    RiskModel.next_review_at < now,
                    RiskModel.status.notin_(
                        [RiskStatus.CLOSED.value]
                    ),
                )
                .subquery()
            )
        ).scalar() or 0

        # Recent risks
        recent_models = (
            self.session.execute(
                select(RiskModel)
                .where(RiskModel.company_id == company_id)
                .order_by(RiskModel.created_at.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )
        recent = [self._to_entity(m) for m in recent_models]

        return {
            "total_risks": total,
            "open_risks": open_count,
            "mitigated_risks": mitigated_count,
            "accepted_risks": accepted_count,
            "by_level": by_level,
            "by_category": by_category,
            "heat_map": heat_map,
            "overdue_reviews": overdue_count,
            "recent_risks": recent,
        }

    # --- Overdue reviews ---

    def find_overdue_reviews(
        self, company_id: Optional[str] = None
    ) -> list[Risk]:
        now = datetime.now(timezone.utc)
        query = (
            select(RiskModel)
            .where(
                RiskModel.next_review_at.isnot(None),
                RiskModel.next_review_at < now,
                RiskModel.status.notin_([RiskStatus.CLOSED.value]),
            )
        )
        if company_id:
            query = query.where(RiskModel.company_id == company_id)

        models = self.session.execute(query).scalars().all()
        return [self._to_entity(m) for m in models]

    # --- Mappers ---

    def _to_entity(self, model: RiskModel) -> Risk:
        return Risk(
            id=model.id,
            company_id=model.company_id,
            title=model.title,
            description=model.description,
            category=RiskCategory(model.category),
            status=RiskStatus(model.status),
            created_by=model.created_by,
            likelihood=model.likelihood,
            impact=model.impact,
            risk_level=RiskLevel(model.risk_level) if model.risk_level else None,
            treatment=(
                RiskTreatment(model.treatment) if model.treatment else None
            ),
            review_cadence=(
                ReviewCadence(model.review_cadence)
                if model.review_cadence
                else None
            ),
            next_review_at=model.next_review_at,
            owner_id=model.owner_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_mitigation(self, model: MitigationPlanModel) -> MitigationPlan:
        return MitigationPlan(
            id=model.id,
            risk_id=model.risk_id,
            description=model.description,
            status=MitigationStatus(model.status),
            owner_id=model.owner_id,
            target_date=model.target_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
