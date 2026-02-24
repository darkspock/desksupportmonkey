from datetime import datetime, timedelta, timezone
from typing import Optional

import ulid
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from src.incident_bc.incident.domain.entities import (
    IncidentTimeline,
    RegulatoryReport,
    SecurityIncident,
)
from src.incident_bc.incident.domain.enums import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    ReportStatus,
    ReportType,
    TimelineEventType,
)
from src.incident_bc.incident.domain.repository import (
    IncidentFilters,
    IncidentRepositoryInterface,
)
from src.incident_bc.incident.infrastructure.models import (
    IncidentAssetModel,
    IncidentTimelineModel,
    IncidentVendorModel,
    PostMortemModel,
    RegulatoryReportModel,
    SecurityIncidentModel,
)


class IncidentRepository(IncidentRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    # --- SecurityIncident ---

    def save(self, incident: SecurityIncident) -> None:
        existing = self.session.execute(
            select(SecurityIncidentModel).where(
                SecurityIncidentModel.id == incident.id
            )
        ).scalar_one_or_none()

        if existing:
            existing.company_id = incident.company_id
            existing.title = incident.title
            existing.description = incident.description
            existing.incident_type = incident.incident_type.value
            existing.severity = incident.severity.value
            existing.status = incident.status.value
            existing.attack_vector = incident.attack_vector
            existing.data_breach_scope = incident.data_breach_scope
            existing.reported_by = incident.reported_by
            existing.assigned_to = incident.assigned_to
            existing.detected_at = incident.detected_at
            existing.close_reason = incident.close_reason
            existing.closed_at = incident.closed_at
        else:
            model = SecurityIncidentModel(
                id=incident.id,
                company_id=incident.company_id,
                title=incident.title,
                description=incident.description,
                incident_type=incident.incident_type.value,
                severity=incident.severity.value,
                status=incident.status.value,
                attack_vector=incident.attack_vector,
                data_breach_scope=incident.data_breach_scope,
                reported_by=incident.reported_by,
                assigned_to=incident.assigned_to,
                detected_at=incident.detected_at,
                close_reason=incident.close_reason,
                closed_at=incident.closed_at,
            )
            self.session.add(model)
        self.session.flush()

    def find_by_id(
        self, incident_id: str, company_id: str
    ) -> Optional[SecurityIncident]:
        model = self.session.execute(
            select(SecurityIncidentModel).where(
                SecurityIncidentModel.id == incident_id,
                SecurityIncidentModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    def find_all(
        self, company_id: str, filters: IncidentFilters
    ) -> tuple[list[SecurityIncident], int]:
        query = select(SecurityIncidentModel).where(
            SecurityIncidentModel.company_id == company_id
        )

        if filters.status:
            query = query.where(SecurityIncidentModel.status == filters.status)
        if filters.severity:
            query = query.where(
                SecurityIncidentModel.severity == filters.severity
            )
        if filters.incident_type:
            query = query.where(
                SecurityIncidentModel.incident_type == filters.incident_type
            )
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                SecurityIncidentModel.title.ilike(search_term)
            )
        if filters.date_from:
            query = query.where(
                SecurityIncidentModel.detected_at >= filters.date_from
            )
        if filters.date_to:
            query = query.where(
                SecurityIncidentModel.detected_at <= filters.date_to
            )

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = self.session.execute(count_query).scalar() or 0

        # Paginate
        offset = (filters.page - 1) * filters.page_size
        query = query.order_by(SecurityIncidentModel.created_at.desc())
        query = query.offset(offset).limit(filters.page_size)

        models = self.session.execute(query).scalars().all()
        return [self._to_entity(m) for m in models], total

    # --- IncidentTimeline ---

    def save_timeline(self, entry: IncidentTimeline) -> None:
        model = IncidentTimelineModel(
            id=entry.id,
            incident_id=entry.incident_id,
            event_type=entry.event_type.value,
            description=entry.description,
            actor_id=entry.actor_id,
            metadata_json=entry.metadata,
        )
        self.session.add(model)
        self.session.flush()

    def find_timeline(self, incident_id: str) -> list[IncidentTimeline]:
        models = (
            self.session.execute(
                select(IncidentTimelineModel)
                .where(IncidentTimelineModel.incident_id == incident_id)
                .order_by(IncidentTimelineModel.created_at.desc())
            )
            .scalars()
            .all()
        )
        return [
            IncidentTimeline(
                id=m.id,
                incident_id=m.incident_id,
                event_type=TimelineEventType(m.event_type),
                description=m.description,
                actor_id=m.actor_id,
                created_at=m.created_at,
                metadata=m.metadata_json,
            )
            for m in models
        ]

    # --- IncidentAsset ---

    def save_incident_asset(
        self,
        incident_id: str,
        asset_id: str,
        impact_description: Optional[str],
    ) -> str:
        link_id = str(ulid.new())
        model = IncidentAssetModel(
            id=link_id,
            incident_id=incident_id,
            asset_id=asset_id,
            impact_description=impact_description,
        )
        self.session.add(model)
        self.session.flush()
        return link_id

    def delete_incident_asset(self, incident_id: str, asset_id: str) -> None:
        self.session.execute(
            select(IncidentAssetModel)
            .where(
                IncidentAssetModel.incident_id == incident_id,
                IncidentAssetModel.asset_id == asset_id,
            )
        )
        self.session.query(IncidentAssetModel).filter(
            IncidentAssetModel.incident_id == incident_id,
            IncidentAssetModel.asset_id == asset_id,
        ).delete()
        self.session.flush()

    def find_assets_by_incident(self, incident_id: str) -> list[dict]:
        models = (
            self.session.execute(
                select(IncidentAssetModel).where(
                    IncidentAssetModel.incident_id == incident_id
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": m.id,
                "asset_id": m.asset_id,
                "impact_description": m.impact_description,
                "created_at": m.created_at,
            }
            for m in models
        ]

    # --- IncidentVendor ---

    def save_incident_vendor(
        self,
        incident_id: str,
        vendor_id: str,
        involvement_description: Optional[str],
    ) -> str:
        link_id = str(ulid.new())
        model = IncidentVendorModel(
            id=link_id,
            incident_id=incident_id,
            vendor_id=vendor_id,
            involvement_description=involvement_description,
        )
        self.session.add(model)
        self.session.flush()
        return link_id

    def delete_incident_vendor(
        self, incident_id: str, vendor_id: str
    ) -> None:
        self.session.query(IncidentVendorModel).filter(
            IncidentVendorModel.incident_id == incident_id,
            IncidentVendorModel.vendor_id == vendor_id,
        ).delete()
        self.session.flush()

    def find_vendors_by_incident(self, incident_id: str) -> list[dict]:
        models = (
            self.session.execute(
                select(IncidentVendorModel).where(
                    IncidentVendorModel.incident_id == incident_id
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": m.id,
                "vendor_id": m.vendor_id,
                "involvement_description": m.involvement_description,
                "created_at": m.created_at,
            }
            for m in models
        ]

    # --- RegulatoryReport ---

    def save_report(self, report: RegulatoryReport) -> None:
        model = RegulatoryReportModel(
            id=report.id,
            incident_id=report.incident_id,
            report_type=report.report_type.value,
            status=report.status.value,
            deadline_at=report.deadline_at,
            generated_at=report.generated_at,
            submitted_at=report.submitted_at,
            file_path=report.file_path,
        )
        self.session.add(model)
        self.session.flush()

    def save_reports_batch(self, reports: list[RegulatoryReport]) -> None:
        for report in reports:
            model = RegulatoryReportModel(
                id=report.id,
                incident_id=report.incident_id,
                report_type=report.report_type.value,
                status=report.status.value,
                deadline_at=report.deadline_at,
                generated_at=report.generated_at,
                submitted_at=report.submitted_at,
                file_path=report.file_path,
            )
            self.session.add(model)
        self.session.flush()

    def update_report(self, report: RegulatoryReport) -> None:
        model = self.session.execute(
            select(RegulatoryReportModel).where(
                RegulatoryReportModel.id == report.id
            )
        ).scalar_one_or_none()
        if model:
            model.status = report.status.value
            model.file_path = report.file_path
            model.generated_at = report.generated_at
            model.submitted_at = report.submitted_at
            self.session.flush()

    def find_report_by_id(
        self, report_id: str, incident_id: str
    ) -> Optional[RegulatoryReport]:
        model = self.session.execute(
            select(RegulatoryReportModel).where(
                RegulatoryReportModel.id == report_id,
                RegulatoryReportModel.incident_id == incident_id,
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._report_to_entity(model)

    def find_reports_by_incident(
        self, incident_id: str
    ) -> list[RegulatoryReport]:
        models = (
            self.session.execute(
                select(RegulatoryReportModel)
                .where(RegulatoryReportModel.incident_id == incident_id)
                .order_by(RegulatoryReportModel.deadline_at.asc())
            )
            .scalars()
            .all()
        )
        return [self._report_to_entity(m) for m in models]

    def find_pending_reports_approaching_deadline(
        self,
    ) -> list[tuple[RegulatoryReport, SecurityIncident]]:
        models = (
            self.session.execute(
                select(RegulatoryReportModel, SecurityIncidentModel)
                .join(
                    SecurityIncidentModel,
                    RegulatoryReportModel.incident_id
                    == SecurityIncidentModel.id,
                )
                .where(
                    RegulatoryReportModel.status.in_(
                        [ReportStatus.PENDING.value, ReportStatus.GENERATED.value]
                    )
                )
                .order_by(RegulatoryReportModel.deadline_at.asc())
            )
            .all()
        )
        return [
            (self._report_to_entity(r), self._to_entity(i))
            for r, i in models
        ]

    # --- PostMortem ---

    def save_postmortem(self, postmortem: dict) -> None:
        existing = self.session.execute(
            select(PostMortemModel).where(
                PostMortemModel.incident_id == postmortem["incident_id"]
            )
        ).scalar_one_or_none()

        if existing:
            existing.root_cause = postmortem.get(
                "root_cause", existing.root_cause
            )
            existing.lessons_learned = postmortem.get(
                "lessons_learned", existing.lessons_learned
            )
            existing.corrective_actions = postmortem.get(
                "corrective_actions", existing.corrective_actions
            )
        else:
            model = PostMortemModel(**postmortem)
            self.session.add(model)
        self.session.flush()

    def find_postmortem_by_incident(
        self, incident_id: str
    ) -> Optional[dict]:
        model = self.session.execute(
            select(PostMortemModel).where(
                PostMortemModel.incident_id == incident_id
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return {
            "id": model.id,
            "incident_id": model.incident_id,
            "root_cause": model.root_cause,
            "lessons_learned": model.lessons_learned,
            "corrective_actions": model.corrective_actions,
            "created_by": model.created_by,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    # --- Dashboard ---

    def get_dashboard_stats(self, company_id: str) -> dict:
        base = select(SecurityIncidentModel).where(
            SecurityIncidentModel.company_id == company_id
        )

        # Active count
        active_count = self.session.execute(
            select(func.count()).select_from(
                base.where(
                    SecurityIncidentModel.status != "closed"
                ).subquery()
            )
        ).scalar() or 0

        # Closed count
        closed_count = self.session.execute(
            select(func.count()).select_from(
                base.where(
                    SecurityIncidentModel.status == "closed"
                ).subquery()
            )
        ).scalar() or 0

        # Active by severity
        severity_rows = self.session.execute(
            select(
                SecurityIncidentModel.severity,
                func.count(),
            )
            .where(
                SecurityIncidentModel.company_id == company_id,
                SecurityIncidentModel.status != "closed",
            )
            .group_by(SecurityIncidentModel.severity)
        ).all()
        active_by_severity = {row[0]: row[1] for row in severity_rows}

        # By type
        type_rows = self.session.execute(
            select(
                SecurityIncidentModel.incident_type,
                func.count(),
            )
            .where(SecurityIncidentModel.company_id == company_id)
            .group_by(SecurityIncidentModel.incident_type)
        ).all()
        by_type = {row[0]: row[1] for row in type_rows}

        # MTTR — average time from detected to closed
        mttr_result = self.session.execute(
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        SecurityIncidentModel.closed_at
                        - SecurityIncidentModel.detected_at,
                    )
                )
            ).where(
                SecurityIncidentModel.company_id == company_id,
                SecurityIncidentModel.status == "closed",
                SecurityIncidentModel.closed_at.isnot(None),
            )
        ).scalar()
        mttr_hours = round(mttr_result / 3600, 1) if mttr_result else None

        # MTTC — average time from detected_at to first status_change to "contained"
        # Subquery: for each incident, find the earliest timeline entry where
        # the status changed to "contained"
        contained_sub = (
            select(
                IncidentTimelineModel.incident_id,
                func.min(IncidentTimelineModel.created_at).label("contained_at"),
            )
            .where(
                IncidentTimelineModel.event_type == "status_change",
                IncidentTimelineModel.metadata_json["new_status"].as_string()
                == "contained",
            )
            .group_by(IncidentTimelineModel.incident_id)
            .subquery()
        )
        mttc_result = self.session.execute(
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        contained_sub.c.contained_at
                        - SecurityIncidentModel.detected_at,
                    )
                )
            )
            .join(
                contained_sub,
                and_(
                    SecurityIncidentModel.id == contained_sub.c.incident_id,
                    SecurityIncidentModel.company_id == company_id,
                ),
            )
        ).scalar()
        mttc_hours = round(mttc_result / 3600, 1) if mttc_result else None

        # Upcoming deadlines — regulatory reports due in next 7 days
        now = datetime.now(timezone.utc)
        seven_days_later = now + timedelta(days=7)
        deadline_rows = (
            self.session.execute(
                select(RegulatoryReportModel, SecurityIncidentModel)
                .join(
                    SecurityIncidentModel,
                    RegulatoryReportModel.incident_id
                    == SecurityIncidentModel.id,
                )
                .where(
                    SecurityIncidentModel.company_id == company_id,
                    RegulatoryReportModel.status.in_(
                        [ReportStatus.PENDING.value, ReportStatus.GENERATED.value]
                    ),
                    RegulatoryReportModel.deadline_at <= seven_days_later,
                    RegulatoryReportModel.deadline_at >= now,
                )
                .order_by(RegulatoryReportModel.deadline_at.asc())
            )
            .all()
        )
        upcoming_deadlines = [
            {
                "incident_id": inc.id,
                "incident_title": inc.title,
                "report_type": report.report_type,
                "deadline_at": report.deadline_at.isoformat(),
                "time_remaining_seconds": max(
                    0,
                    int((report.deadline_at - now).total_seconds()),
                ),
            }
            for report, inc in deadline_rows
        ]

        # Recent incidents
        recent_models = (
            self.session.execute(
                select(SecurityIncidentModel)
                .where(SecurityIncidentModel.company_id == company_id)
                .order_by(SecurityIncidentModel.created_at.desc())
                .limit(10)
            )
            .scalars()
            .all()
        )
        recent = [self._to_entity(m) for m in recent_models]

        return {
            "total_active": active_count,
            "total_closed": closed_count,
            "active_by_severity": active_by_severity,
            "by_type": by_type,
            "mttc_hours": mttc_hours,
            "mttr_hours": mttr_hours,
            "upcoming_deadlines": upcoming_deadlines,
            "recent_incidents": recent,
        }

    # --- Employee view ---

    def find_my_incidents(
        self, user_id: str, company_id: str
    ) -> list[SecurityIncident]:
        models = (
            self.session.execute(
                select(SecurityIncidentModel)
                .where(
                    SecurityIncidentModel.company_id == company_id,
                    SecurityIncidentModel.reported_by == user_id,
                )
                .order_by(SecurityIncidentModel.created_at.desc())
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    # --- Helpers ---

    def _to_entity(self, model: SecurityIncidentModel) -> SecurityIncident:
        return SecurityIncident(
            id=model.id,
            company_id=model.company_id,
            title=model.title,
            description=model.description,
            incident_type=IncidentType(model.incident_type),
            severity=IncidentSeverity(model.severity),
            status=IncidentStatus(model.status),
            attack_vector=model.attack_vector,
            data_breach_scope=model.data_breach_scope,
            reported_by=model.reported_by,
            assigned_to=model.assigned_to,
            detected_at=model.detected_at,
            close_reason=model.close_reason,
            created_at=model.created_at,
            updated_at=model.updated_at,
            closed_at=model.closed_at,
        )

    def _report_to_entity(self, model: RegulatoryReportModel) -> RegulatoryReport:
        return RegulatoryReport(
            id=model.id,
            incident_id=model.incident_id,
            report_type=ReportType(model.report_type),
            status=ReportStatus(model.status),
            deadline_at=model.deadline_at,
            generated_at=model.generated_at,
            submitted_at=model.submitted_at,
            file_path=model.file_path,
        )
