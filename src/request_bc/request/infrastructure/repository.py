from typing import Optional

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from src.request_bc.request.domain.entities import (
    RequestComment,
    RequestEvent,
    RequestNote,
    ServiceRequest,
)
from src.request_bc.request.domain.enums import RequestPriority, RequestStatus, RequestType
from src.request_bc.request.domain.repository import RequestRepositoryInterface
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
        else:
            model = ServiceRequestModel(
                id=request.id,
                company_id=request.company_id,
                created_by=request.created_by,
                assigned_to=request.assigned_to,
                type=request.type.value,
                title=request.title,
                description=request.description,
                status=request.status.value,
                priority=request.priority.value,
                data=request.data,
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
    ) -> tuple[list[ServiceRequest], int]:
        stmt = select(ServiceRequestModel).where(
            ServiceRequestModel.company_id == company_id
        )

        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    ServiceRequestModel.title.ilike(pattern),
                    ServiceRequestModel.description.ilike(pattern),
                )
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
        return [self._to_entity(m) for m in models], total

    def find_by_created_by(
        self,
        user_id: str,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> tuple[list[ServiceRequest], int]:
        stmt = select(ServiceRequestModel).where(
            ServiceRequestModel.company_id == company_id,
            ServiceRequestModel.created_by == user_id,
        )
        if status is not None:
            stmt = stmt.where(ServiceRequestModel.status == status)

        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()

        stmt = stmt.order_by(ServiceRequestModel.created_at.desc())
        offset = (page - 1) * page_size
        models = self.session.execute(
            stmt.offset(offset).limit(page_size)
        ).scalars().all()
        return [self._to_entity(m) for m in models], total

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
            data=model.data,
            resolved_at=model.resolved_at,
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
