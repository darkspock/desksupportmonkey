from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import case, extract, func, or_, select
from sqlalchemy.orm import Session

from src.request_bc.request.domain.entities import (
    RequestComment,
    RequestEvent,
    RequestNote,
    ServiceRequest,
)
from src.request_bc.request.domain.enums import RequestPriority, RequestStatus, RequestType
from src.request_bc.request.domain.repository import RequestRepositoryInterface
from src.auth_bc.user.infrastructure.models import UserModel
from src.request_bc.request.infrastructure.models import (
    RequestCommentModel,
    RequestEventModel,
    RequestNoteModel,
    ServiceRequestModel,
)


class RequestRepository(RequestRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, request: ServiceRequest) -> ServiceRequest:
        existing = self.session.execute(
            select(ServiceRequestModel).where(ServiceRequestModel.id == request.id)
        ).scalar_one_or_none()
        if existing:
            existing.assigned_to = request.assigned_to
            existing.status = request.status.value
            existing.priority = request.priority.value
            existing.resolved_at = request.resolved_at
            existing.first_response_at = request.first_response_at
            existing.custom_fields_data = request.custom_fields_data or {}
        else:
            model = ServiceRequestModel(
                id=request.id,
                company_id=request.company_id,
                created_by=request.created_by,
                assigned_to=request.assigned_to,
                type=request.type.value,
                subtype=request.subtype,
                title=request.title,
                description=request.description,
                status=request.status.value,
                priority=request.priority.value,
                data=request.data,
                custom_fields_data=request.custom_fields_data or {},
                resolved_at=request.resolved_at,
            )
            self.session.add(model)
            existing = model
        self.session.flush()
        self.session.refresh(existing)
        return self._to_entity(existing)

    def find_by_id(self, request_id: str, company_id: str) -> Optional[ServiceRequest]:
        model = self.session.execute(
            select(ServiceRequestModel).where(
                ServiceRequestModel.id == request_id,
                ServiceRequestModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def save_event(self, event: RequestEvent) -> RequestEvent:
        model = RequestEventModel(
            id=event.id,
            request_id=event.request_id,
            event_type=event.event_type,
            data=event.data,
            performed_by=event.performed_by,
        )
        self.session.add(model)
        self.session.flush()
        return event

    def find_events(self, request_id: str, company_id: str) -> list[RequestEvent]:
        models = (
            self.session.execute(
                select(RequestEventModel)
                .join(
                    ServiceRequestModel,
                    ServiceRequestModel.id == RequestEventModel.request_id,
                )
                .where(
                    RequestEventModel.request_id == request_id,
                    ServiceRequestModel.company_id == company_id,
                )
                .order_by(RequestEventModel.created_at.desc())
            )
            .scalars()
            .all()
        )
        return [self._event_to_entity(m) for m in models]

    def count_comments(self, request_id: str) -> int:
        result = self.session.execute(
            select(func.count()).select_from(RequestCommentModel).where(
                RequestCommentModel.request_id == request_id
            )
        ).scalar()
        return result or 0

    def find_all(
        self,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        type: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[str] = None,
        subtype: Optional[str] = None,
        custom_field_filters: Optional[dict[str, str]] = None,
        custom_field_search_keys: Optional[list[str]] = None,
    ) -> tuple[list[ServiceRequest], int]:
        stmt = select(ServiceRequestModel).where(
            ServiceRequestModel.company_id == company_id
        )

        if search:
            pattern = f"%{search}%"
            creator = UserModel.__table__.alias("creator")
            or_conditions = [
                ServiceRequestModel.title.ilike(pattern),
                ServiceRequestModel.description.ilike(pattern),
                ServiceRequestModel.id.ilike(pattern),
                creator.c.name.ilike(pattern),
                creator.c.email.ilike(pattern),
            ]
            if custom_field_search_keys:
                for cf_key in custom_field_search_keys:
                    or_conditions.append(
                        ServiceRequestModel.custom_fields_data[cf_key].as_string().ilike(pattern)
                    )
            stmt = stmt.outerjoin(
                creator, ServiceRequestModel.created_by == creator.c.id,
            ).where(or_(*or_conditions))

        if custom_field_filters:
            for key, value in custom_field_filters.items():
                stmt = stmt.where(
                    ServiceRequestModel.custom_fields_data[key].as_string() == value
                )

        if status is not None:
            stmt = stmt.where(ServiceRequestModel.status == status)
        if type is not None:
            stmt = stmt.where(ServiceRequestModel.type == type)
        if priority is not None:
            stmt = stmt.where(ServiceRequestModel.priority == priority)
        if assigned_to is not None:
            if assigned_to == "none":
                stmt = stmt.where(ServiceRequestModel.assigned_to.is_(None))
            else:
                stmt = stmt.where(ServiceRequestModel.assigned_to == assigned_to)
        if subtype is not None:
            stmt = stmt.where(ServiceRequestModel.subtype == subtype)

        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()

        priority_order = case(
            (ServiceRequestModel.priority == "urgent", 4),
            (ServiceRequestModel.priority == "high", 3),
            (ServiceRequestModel.priority == "medium", 2),
            (ServiceRequestModel.priority == "low", 1),
            else_=0,
        )
        stmt = stmt.order_by(priority_order.desc(), ServiceRequestModel.created_at.asc())

        offset = (page - 1) * page_size
        models = self.session.execute(
            stmt.offset(offset).limit(page_size)
        ).scalars().all()
        return [self._to_entity(m) for m in models], total or 0

    def find_by_created_by(
        self,
        user_id: str,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        subtype: Optional[str] = None,
    ) -> tuple[list[ServiceRequest], int]:
        stmt = select(ServiceRequestModel).where(
            ServiceRequestModel.company_id == company_id,
            ServiceRequestModel.created_by == user_id,
        )
        if status is not None:
            stmt = stmt.where(ServiceRequestModel.status == status)
        if subtype is not None:
            stmt = stmt.where(ServiceRequestModel.subtype == subtype)

        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()

        stmt = stmt.order_by(ServiceRequestModel.created_at.desc())
        offset = (page - 1) * page_size
        models = self.session.execute(
            stmt.offset(offset).limit(page_size)
        ).scalars().all()
        return [self._to_entity(m) for m in models], total or 0

    def save_comment(self, comment: RequestComment) -> RequestComment:
        model = RequestCommentModel(
            id=comment.id,
            request_id=comment.request_id,
            author_id=comment.author_id,
            body=comment.body,
        )
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return self._comment_to_entity(model)

    def find_comments(self, request_id: str) -> list[RequestComment]:
        models = self.session.execute(
            select(RequestCommentModel)
            .where(RequestCommentModel.request_id == request_id)
            .order_by(RequestCommentModel.created_at.asc())
        ).scalars().all()
        return [self._comment_to_entity(m) for m in models]

    def save_note(self, note: RequestNote) -> RequestNote:
        model = RequestNoteModel(
            id=note.id,
            request_id=note.request_id,
            author_id=note.author_id,
            body=note.body,
        )
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return self._note_to_entity(model)

    def find_notes(self, request_id: str) -> list[RequestNote]:
        models = self.session.execute(
            select(RequestNoteModel)
            .where(RequestNoteModel.request_id == request_id)
            .order_by(RequestNoteModel.created_at.asc())
        ).scalars().all()
        return [self._note_to_entity(m) for m in models]

    def count_by_status(self, company_id: str) -> dict[str, int]:
        rows = self.session.execute(
            select(
                ServiceRequestModel.status,
                func.count().label("cnt"),
            ).where(
                ServiceRequestModel.company_id == company_id
            ).group_by(ServiceRequestModel.status)
        ).all()
        result = {s.value: 0 for s in RequestStatus}
        for row in rows:
            result[row[0]] = row[1]
        return result

    def count_by_type(self, company_id: str) -> dict[str, int]:
        rows = self.session.execute(
            select(
                ServiceRequestModel.type,
                func.count().label("cnt"),
            ).where(
                ServiceRequestModel.company_id == company_id
            ).group_by(ServiceRequestModel.type)
        ).all()
        result = {t.value: 0 for t in RequestType}
        for row in rows:
            result[row[0]] = row[1]
        return result

    def count_by_priority(self, company_id: str) -> dict[str, int]:
        rows = self.session.execute(
            select(
                ServiceRequestModel.priority,
                func.count().label("cnt"),
            ).where(
                ServiceRequestModel.company_id == company_id
            ).group_by(ServiceRequestModel.priority)
        ).all()
        result = {p.value: 0 for p in RequestPriority}
        for row in rows:
            result[row[0]] = row[1]
        return result

    def avg_resolution_time(
        self, company_id: str, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> Optional[float]:
        stmt = select(
            func.avg(
                extract("epoch", ServiceRequestModel.resolved_at - ServiceRequestModel.created_at) / 3600
            )
        ).where(
            ServiceRequestModel.company_id == company_id,
            ServiceRequestModel.resolved_at.isnot(None),
        )
        if from_date:
            stmt = stmt.where(ServiceRequestModel.resolved_at >= datetime(from_date.year, from_date.month, from_date.day, tzinfo=timezone.utc))
        if to_date:
            stmt = stmt.where(ServiceRequestModel.resolved_at <= datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59, tzinfo=timezone.utc))
        result = self.session.execute(stmt).scalar()
        return round(float(result), 2) if result is not None else None

    def avg_resolution_time_by_technician(
        self, company_id: str, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> list[dict]:
        stmt = select(
            ServiceRequestModel.assigned_to,
            func.avg(
                extract("epoch", ServiceRequestModel.resolved_at - ServiceRequestModel.created_at) / 3600
            ).label("avg_hours"),
            func.count().label("resolved_count"),
        ).where(
            ServiceRequestModel.company_id == company_id,
            ServiceRequestModel.resolved_at.isnot(None),
            ServiceRequestModel.assigned_to.isnot(None),
        ).group_by(ServiceRequestModel.assigned_to)
        if from_date:
            stmt = stmt.where(ServiceRequestModel.resolved_at >= datetime(from_date.year, from_date.month, from_date.day, tzinfo=timezone.utc))
        if to_date:
            stmt = stmt.where(ServiceRequestModel.resolved_at <= datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59, tzinfo=timezone.utc))
        rows = self.session.execute(stmt).all()
        return [
            {
                "technician_id": row[0],
                "avg_hours": round(float(row[1]), 2),
                "resolved_count": row[2],
            }
            for row in rows
        ]

    def count_by_period(
        self, company_id: str, bucket: str, from_date: date, to_date: date
    ) -> list[dict]:
        period = func.date_trunc(bucket, ServiceRequestModel.created_at).label("period")
        stmt = select(
            period,
            ServiceRequestModel.type,
            func.count().label("cnt"),
        ).where(
            ServiceRequestModel.company_id == company_id,
            ServiceRequestModel.created_at >= datetime(from_date.year, from_date.month, from_date.day, tzinfo=timezone.utc),
            ServiceRequestModel.created_at <= datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59, tzinfo=timezone.utc),
        ).group_by(period, ServiceRequestModel.type).order_by(period)
        rows = self.session.execute(stmt).all()
        return [
            {
                "period": row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0]),
                "type": row[1],
                "count": row[2],
            }
            for row in rows
        ]

    def find_open_requests_with_age(self, company_id: str) -> list[dict]:
        stmt = select(
            ServiceRequestModel.id,
            ServiceRequestModel.title,
            ServiceRequestModel.type,
            ServiceRequestModel.priority,
            ServiceRequestModel.status,
            ServiceRequestModel.assigned_to,
            ServiceRequestModel.created_at,
            (extract("epoch", func.now() - ServiceRequestModel.created_at) / 3600).label("hours_open"),
        ).where(
            ServiceRequestModel.company_id == company_id,
            ServiceRequestModel.status.in_([
                RequestStatus.SUBMITTED.value,
                RequestStatus.IN_REVIEW.value,
                RequestStatus.IN_PROGRESS.value,
            ]),
        ).order_by(
            (extract("epoch", func.now() - ServiceRequestModel.created_at) / 3600).desc()
        )
        rows = self.session.execute(stmt).all()
        return [
            {
                "id": row[0],
                "title": row[1],
                "type": row[2],
                "priority": row[3],
                "status": row[4],
                "assigned_to": row[5],
                "created_at": row[6],
                "hours_open": round(float(row[7]), 2),
            }
            for row in rows
        ]

    @staticmethod
    def _to_entity(model: ServiceRequestModel) -> ServiceRequest:
        return ServiceRequest(
            id=model.id,
            company_id=model.company_id,
            created_by=model.created_by,
            type=RequestType(model.type),
            title=model.title,
            description=model.description,
            status=RequestStatus(model.status),
            priority=RequestPriority(model.priority),
            assigned_to=model.assigned_to,
            subtype=model.subtype,
            data=model.data,
            custom_fields_data=model.custom_fields_data or {},
            resolved_at=model.resolved_at,
            first_response_at=model.first_response_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _event_to_entity(model: RequestEventModel) -> RequestEvent:
        return RequestEvent(
            id=model.id,
            request_id=model.request_id,
            event_type=model.event_type,
            data=model.data,
            performed_by=model.performed_by,
            created_at=model.created_at,
        )

    @staticmethod
    def _comment_to_entity(model: RequestCommentModel) -> RequestComment:
        return RequestComment(
            id=model.id,
            request_id=model.request_id,
            author_id=model.author_id,
            body=model.body,
            created_at=model.created_at,
        )

    @staticmethod
    def _note_to_entity(model: RequestNoteModel) -> RequestNote:
        return RequestNote(
            id=model.id,
            request_id=model.request_id,
            author_id=model.author_id,
            body=model.body,
            created_at=model.created_at,
        )
