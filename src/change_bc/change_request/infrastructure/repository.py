from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from src.change_bc.change_request.domain.entities import (
    ChangeAsset,
    ChangeEvent,
    ChangeRequest,
    PostImplementationReview,
)
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
    ChangeType,
    PIROutcome,
)
from src.change_bc.change_request.domain.repository import (
    ChangeRequestFilters,
    ChangeRequestRepositoryInterface,
)
from src.change_bc.change_request.infrastructure.models import (
    ChangeAssetModel,
    ChangeEventModel,
    ChangeRequestModel,
    PostImplementationReviewModel,
)


class ChangeRequestRepository(ChangeRequestRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, change: ChangeRequest) -> None:
        existing = self.session.execute(
            select(ChangeRequestModel).where(
                ChangeRequestModel.id == change.id
            )
        ).scalar_one_or_none()

        if existing:
            existing.company_id = change.company_id
            existing.title = change.title
            existing.description = change.description
            existing.change_type = change.change_type.value
            existing.status = change.status.value
            existing.business_justification = change.business_justification
            existing.risk_assessment = change.risk_assessment
            existing.rollback_plan = change.rollback_plan
            existing.planned_date = change.planned_date
            existing.requested_by = change.requested_by
            existing.assigned_to = change.assigned_to
            existing.approved_by = change.approved_by
            existing.approved_at = change.approved_at
            existing.rejected_by = change.rejected_by
            existing.rejected_at = change.rejected_at
            existing.rejection_reason = change.rejection_reason
            existing.started_at = change.started_at
            existing.implemented_at = change.implemented_at
            existing.implementation_notes = change.implementation_notes
            existing.rolled_back_at = change.rolled_back_at
            existing.rollback_reason = change.rollback_reason
            existing.closed_at = change.closed_at
        else:
            model = ChangeRequestModel(
                id=change.id,
                company_id=change.company_id,
                title=change.title,
                description=change.description,
                change_type=change.change_type.value,
                status=change.status.value,
                business_justification=change.business_justification,
                risk_assessment=change.risk_assessment,
                rollback_plan=change.rollback_plan,
                planned_date=change.planned_date,
                requested_by=change.requested_by,
                assigned_to=change.assigned_to,
                approved_by=change.approved_by,
                approved_at=change.approved_at,
                rejected_by=change.rejected_by,
                rejected_at=change.rejected_at,
                rejection_reason=change.rejection_reason,
                started_at=change.started_at,
                implemented_at=change.implemented_at,
                implementation_notes=change.implementation_notes,
                rolled_back_at=change.rolled_back_at,
                rollback_reason=change.rollback_reason,
                closed_at=change.closed_at,
            )
            self.session.add(model)
        self.session.flush()

    def find_by_id(
        self, change_id: str, company_id: str
    ) -> Optional[ChangeRequest]:
        model = self.session.execute(
            select(ChangeRequestModel).where(
                ChangeRequestModel.id == change_id,
                ChangeRequestModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    def find_all(
        self, company_id: str, filters: ChangeRequestFilters
    ) -> tuple[list[ChangeRequest], int]:
        query = select(ChangeRequestModel).where(
            ChangeRequestModel.company_id == company_id
        )

        if filters.status:
            query = query.where(ChangeRequestModel.status == filters.status)
        if filters.change_type:
            query = query.where(
                ChangeRequestModel.change_type == filters.change_type
            )
        if filters.assigned_to:
            query = query.where(
                ChangeRequestModel.assigned_to == filters.assigned_to
            )
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    ChangeRequestModel.title.ilike(search_term),
                    ChangeRequestModel.description.ilike(search_term),
                )
            )
        if filters.date_from:
            query = query.where(
                ChangeRequestModel.planned_date >= filters.date_from
            )
        if filters.date_to:
            query = query.where(
                ChangeRequestModel.planned_date <= filters.date_to
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = self.session.execute(count_query).scalar() or 0

        offset = (filters.page - 1) * filters.page_size
        query = query.order_by(ChangeRequestModel.created_at.desc())
        query = query.offset(offset).limit(filters.page_size)

        models = self.session.execute(query).scalars().all()
        return [self._to_entity(m) for m in models], total

    def save_event(self, event: ChangeEvent) -> None:
        model = ChangeEventModel(
            id=event.id,
            change_request_id=event.change_request_id,
            event_type=event.event_type.value,
            description=event.description,
            actor_id=event.actor_id,
            metadata_json=event.metadata,
        )
        self.session.add(model)
        self.session.flush()

    def find_events(self, change_request_id: str) -> list[ChangeEvent]:
        models = (
            self.session.execute(
                select(ChangeEventModel)
                .where(
                    ChangeEventModel.change_request_id == change_request_id
                )
                .order_by(ChangeEventModel.created_at.asc())
            )
            .scalars()
            .all()
        )
        return [self._to_event_entity(m) for m in models]

    # ChangeAsset methods

    def save_change_asset(self, change_asset: ChangeAsset) -> None:
        model = ChangeAssetModel(
            id=change_asset.id,
            change_request_id=change_asset.change_request_id,
            asset_id=change_asset.asset_id,
        )
        self.session.add(model)
        self.session.flush()

    def delete_change_asset(
        self, change_request_id: str, asset_id: str
    ) -> None:
        self.session.query(ChangeAssetModel).filter(
            ChangeAssetModel.change_request_id == change_request_id,
            ChangeAssetModel.asset_id == asset_id,
        ).delete()
        self.session.flush()

    def find_assets_by_change(
        self, change_request_id: str
    ) -> list[ChangeAsset]:
        models = (
            self.session.execute(
                select(ChangeAssetModel).where(
                    ChangeAssetModel.change_request_id
                    == change_request_id
                )
            )
            .scalars()
            .all()
        )
        return [
            ChangeAsset(
                id=m.id,
                change_request_id=m.change_request_id,
                asset_id=m.asset_id,
                created_at=m.created_at,
            )
            for m in models
        ]

    @staticmethod
    def _to_entity(model: ChangeRequestModel) -> ChangeRequest:
        return ChangeRequest(
            id=model.id,
            company_id=model.company_id,
            title=model.title,
            description=model.description,
            change_type=ChangeType(model.change_type),
            status=ChangeStatus(model.status),
            business_justification=model.business_justification,
            risk_assessment=model.risk_assessment,
            rollback_plan=model.rollback_plan,
            planned_date=model.planned_date,
            requested_by=model.requested_by,
            assigned_to=model.assigned_to,
            approved_by=model.approved_by,
            approved_at=model.approved_at,
            rejected_by=model.rejected_by,
            rejected_at=model.rejected_at,
            rejection_reason=model.rejection_reason,
            started_at=model.started_at,
            implemented_at=model.implemented_at,
            implementation_notes=model.implementation_notes,
            rolled_back_at=model.rolled_back_at,
            rollback_reason=model.rollback_reason,
            closed_at=model.closed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_event_entity(model: ChangeEventModel) -> ChangeEvent:
        return ChangeEvent(
            id=model.id,
            change_request_id=model.change_request_id,
            event_type=ChangeEventType(model.event_type),
            description=model.description,
            actor_id=model.actor_id,
            created_at=model.created_at,
            metadata=model.metadata_json,
        )

    # Dashboard methods

    def get_dashboard_data(self, company_id: str) -> dict:
        now = datetime.now(timezone.utc)

        # Status counts
        status_rows = self.session.execute(
            select(
                ChangeRequestModel.status,
                func.count().label("cnt"),
            )
            .where(ChangeRequestModel.company_id == company_id)
            .group_by(ChangeRequestModel.status)
        ).all()
        status_counts = {s.value: 0 for s in ChangeStatus}
        for row in status_rows:
            status_counts[row[0]] = row[1]

        # Type counts
        type_rows = self.session.execute(
            select(
                ChangeRequestModel.change_type,
                func.count().label("cnt"),
            )
            .where(ChangeRequestModel.company_id == company_id)
            .group_by(ChangeRequestModel.change_type)
        ).all()
        type_counts = {t.value: 0 for t in ChangeType}
        for row in type_rows:
            type_counts[row[0]] = row[1]

        # Upcoming scheduled (next 30 days)
        upcoming_models = (
            self.session.execute(
                select(ChangeRequestModel)
                .where(
                    ChangeRequestModel.company_id == company_id,
                    ChangeRequestModel.status == ChangeStatus.SCHEDULED.value,
                    ChangeRequestModel.planned_date >= now,
                    ChangeRequestModel.planned_date
                    <= now + timedelta(days=30),
                )
                .order_by(ChangeRequestModel.planned_date.asc())
                .limit(20)
            )
            .scalars()
            .all()
        )

        # Recently implemented (last 30 days) with PIR outcome
        recent_rows = self.session.execute(
            select(
                ChangeRequestModel.id,
                ChangeRequestModel.title,
                ChangeRequestModel.change_type,
                ChangeRequestModel.implemented_at,
                PostImplementationReviewModel.outcome,
            )
            .outerjoin(
                PostImplementationReviewModel,
                PostImplementationReviewModel.change_request_id
                == ChangeRequestModel.id,
            )
            .where(
                ChangeRequestModel.company_id == company_id,
                ChangeRequestModel.implemented_at.isnot(None),
                ChangeRequestModel.implemented_at
                >= now - timedelta(days=30),
            )
            .order_by(ChangeRequestModel.implemented_at.desc())
            .limit(20)
        ).all()

        recently_implemented = [
            {
                "id": row[0],
                "title": row[1],
                "change_type": row[2],
                "implemented_at": row[3],
                "pir_outcome": row[4],
            }
            for row in recent_rows
        ]

        # Rolled back last 90 days
        rolled_back_90 = self.session.execute(
            select(func.count())
            .select_from(ChangeRequestModel)
            .where(
                ChangeRequestModel.company_id == company_id,
                ChangeRequestModel.status
                == ChangeStatus.ROLLED_BACK.value,
                ChangeRequestModel.rolled_back_at
                >= now - timedelta(days=90),
            )
        ).scalar() or 0

        # Scheduled this week
        today = now.date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        scheduled_this_week = self.session.execute(
            select(func.count())
            .select_from(ChangeRequestModel)
            .where(
                ChangeRequestModel.company_id == company_id,
                ChangeRequestModel.status
                == ChangeStatus.SCHEDULED.value,
                func.date(ChangeRequestModel.planned_date)
                >= week_start,
                func.date(ChangeRequestModel.planned_date)
                <= week_end,
            )
        ).scalar() or 0

        return {
            "status_counts": status_counts,
            "type_counts": type_counts,
            "upcoming_scheduled": [
                self._to_entity(m) for m in upcoming_models
            ],
            "recently_implemented": recently_implemented,
            "rolled_back_90_days": rolled_back_90,
            "scheduled_this_week": scheduled_this_week,
        }

    # PostImplementationReview methods

    def save_pir(self, pir: PostImplementationReview) -> None:
        model = PostImplementationReviewModel(
            id=pir.id,
            change_request_id=pir.change_request_id,
            outcome=pir.outcome.value,
            issues_found=pir.issues_found,
            lessons_learned=pir.lessons_learned,
            follow_up_actions=pir.follow_up_actions,
            created_by=pir.created_by,
        )
        self.session.add(model)
        self.session.flush()

    def find_pir_by_change(
        self, change_request_id: str
    ) -> Optional[PostImplementationReview]:
        model = self.session.execute(
            select(PostImplementationReviewModel).where(
                PostImplementationReviewModel.change_request_id
                == change_request_id
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return PostImplementationReview(
            id=model.id,
            change_request_id=model.change_request_id,
            outcome=PIROutcome(model.outcome),
            issues_found=model.issues_found,
            lessons_learned=model.lessons_learned,
            follow_up_actions=model.follow_up_actions,
            created_by=model.created_by,
            created_at=model.created_at,
        )
