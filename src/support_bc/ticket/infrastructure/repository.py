from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from src.support_bc.ticket.domain.entities import SupportTicket, TicketMessage
from src.support_bc.ticket.domain.enums import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from src.support_bc.ticket.domain.repository import SupportTicketRepositoryInterface
from src.support_bc.ticket.infrastructure.models import (
    SupportTicketModel,
    TicketMessageModel,
)


class SupportTicketRepository(SupportTicketRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, ticket: SupportTicket) -> SupportTicket:
        existing = self.session.get(SupportTicketModel, ticket.id)
        if existing:
            existing.status = ticket.status.value
            existing.priority = ticket.priority.value
            existing.resolved_at = ticket.resolved_at
            existing.closed_at = ticket.closed_at
            existing.satisfaction_rating = ticket.satisfaction_rating
            existing.satisfaction_comment = ticket.satisfaction_comment
            existing.rated_at = ticket.rated_at
            self.session.flush()
            self.session.refresh(existing)
            return self._to_entity(existing)
        else:
            seq = self.session.execute(
                text("SELECT nextval('support_ticket_ref_seq')")
            ).scalar()
            reference = f"SUP-{seq:04d}"

            model = SupportTicketModel(
                id=ticket.id,
                reference=reference,
                company_id=ticket.company_id,
                created_by=ticket.created_by,
                category=ticket.category.value,
                subject=ticket.subject,
                description=ticket.description,
                status=ticket.status.value,
                priority=ticket.priority.value,
                ai_conversation_summary=ticket.ai_conversation_summary,
            )
            self.session.add(model)
            self.session.flush()
            self.session.refresh(model)
            return self._to_entity(model)

    def find_by_id(
        self, ticket_id: str, company_id: str
    ) -> Optional[SupportTicket]:
        model = self.session.execute(
            select(SupportTicketModel).where(
                SupportTicketModel.id == ticket_id,
                SupportTicketModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_id_any_company(self, ticket_id: str) -> Optional[SupportTicket]:
        model = self.session.get(SupportTicketModel, ticket_id)
        return self._to_entity(model) if model else None

    ALLOWED_SORT_COLUMNS = {
        'reference': SupportTicketModel.reference,
        'subject': SupportTicketModel.subject,
        'status': SupportTicketModel.status,
        'priority': SupportTicketModel.priority,
        'category': SupportTicketModel.category,
        'created_at': SupportTicketModel.created_at,
        'updated_at': SupportTicketModel.updated_at,
    }

    def find_all(
        self,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        company_id: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> tuple[list[SupportTicket], int]:
        query = select(SupportTicketModel)
        if status:
            query = query.where(SupportTicketModel.status == status)
        if category:
            query = query.where(SupportTicketModel.category == category)
        if priority:
            query = query.where(SupportTicketModel.priority == priority)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                SupportTicketModel.subject.ilike(pattern)
                | SupportTicketModel.reference.ilike(pattern)
            )
        if company_id:
            query = query.where(SupportTicketModel.company_id == company_id)

        total = (
            self.session.execute(
                select(func.count()).select_from(query.subquery())
            ).scalar()
            or 0
        )

        if sort_by and sort_by in self.ALLOWED_SORT_COLUMNS:
            col = self.ALLOWED_SORT_COLUMNS[sort_by]
            query = query.order_by(col.asc() if sort_order == 'asc' else col.desc())
        else:
            query = query.order_by(SupportTicketModel.created_at.desc())

        query = query.offset((page - 1) * page_size).limit(page_size)
        models = self.session.execute(query).scalars().all()
        return [self._to_entity(m) for m in models], total

    def find_by_company(
        self,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> tuple[list[SupportTicket], int]:
        query = select(SupportTicketModel).where(
            SupportTicketModel.company_id == company_id
        )
        if status:
            query = query.where(SupportTicketModel.status == status)
        if category:
            query = query.where(SupportTicketModel.category == category)

        total = (
            self.session.execute(
                select(func.count()).select_from(query.subquery())
            ).scalar()
            or 0
        )
        query = query.order_by(SupportTicketModel.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        models = self.session.execute(query).scalars().all()
        return [self._to_entity(m) for m in models], total

    def find_by_created_by(
        self,
        user_id: str,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str] = None,
    ) -> tuple[list[SupportTicket], int]:
        query = select(SupportTicketModel).where(
            SupportTicketModel.created_by == user_id,
            SupportTicketModel.company_id == company_id,
        )
        if status:
            query = query.where(SupportTicketModel.status == status)

        total = (
            self.session.execute(
                select(func.count()).select_from(query.subquery())
            ).scalar()
            or 0
        )
        query = query.order_by(SupportTicketModel.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        models = self.session.execute(query).scalars().all()
        return [self._to_entity(m) for m in models], total

    def find_resolved_older_than_days(self, days: int) -> list[SupportTicket]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        models = (
            self.session.execute(
                select(SupportTicketModel).where(
                    SupportTicketModel.status == TicketStatus.RESOLVED.value,
                    SupportTicketModel.resolved_at < cutoff,
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def find_stale_older_than_days(self, days: int) -> list[SupportTicket]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        active_statuses = [
            TicketStatus.OPEN.value,
            TicketStatus.IN_PROGRESS.value,
            TicketStatus.WAITING_ON_CUSTOMER.value,
        ]
        models = (
            self.session.execute(
                select(SupportTicketModel).where(
                    SupportTicketModel.status.in_(active_statuses),
                    SupportTicketModel.updated_at < cutoff,
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def save_message(self, message: TicketMessage) -> TicketMessage:
        model = TicketMessageModel(
            id=message.id,
            ticket_id=message.ticket_id,
            author_id=message.author_id,
            body=message.body,
            is_from_platform=message.is_from_platform,
        )
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return self._message_to_entity(model)

    def find_messages(self, ticket_id: str) -> list[TicketMessage]:
        models = (
            self.session.execute(
                select(TicketMessageModel)
                .where(TicketMessageModel.ticket_id == ticket_id)
                .order_by(TicketMessageModel.created_at.asc())
            )
            .scalars()
            .all()
        )
        return [self._message_to_entity(m) for m in models]

    def has_unread_platform_messages(
        self, ticket_id: str, last_read_at: Optional[str] = None
    ) -> bool:
        query = select(func.count()).where(
            TicketMessageModel.ticket_id == ticket_id,
            TicketMessageModel.is_from_platform.is_(True),
        )
        if last_read_at:
            query = query.where(TicketMessageModel.created_at > last_read_at)
        count = self.session.execute(query).scalar() or 0
        return count > 0

    def count_by_status(self) -> dict[str, int]:
        result: dict[str, int] = {s.value: 0 for s in TicketStatus}
        rows = self.session.execute(
            select(
                SupportTicketModel.status,
                func.count().label("cnt"),
            ).group_by(SupportTicketModel.status)
        ).all()
        for row in rows:
            result[row[0]] = row[1]
        return result

    def get_avg_satisfaction(self) -> Optional[float]:
        result = self.session.execute(
            select(func.avg(SupportTicketModel.satisfaction_rating)).where(
                SupportTicketModel.satisfaction_rating.isnot(None)
            )
        ).scalar()
        return round(float(result), 2) if result is not None else None

    @staticmethod
    def _to_entity(model: SupportTicketModel) -> SupportTicket:
        return SupportTicket(
            id=model.id,
            reference=model.reference,
            company_id=model.company_id,
            created_by=model.created_by,
            category=TicketCategory(model.category),
            subject=model.subject,
            description=model.description,
            status=TicketStatus(model.status),
            priority=TicketPriority(model.priority),
            ai_conversation_summary=model.ai_conversation_summary,
            resolved_at=model.resolved_at,
            closed_at=model.closed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            satisfaction_rating=model.satisfaction_rating,
            satisfaction_comment=model.satisfaction_comment,
            rated_at=model.rated_at,
        )

    @staticmethod
    def _message_to_entity(model: TicketMessageModel) -> TicketMessage:
        return TicketMessage(
            id=model.id,
            ticket_id=model.ticket_id,
            author_id=model.author_id,
            body=model.body,
            is_from_platform=model.is_from_platform,
            created_at=model.created_at,
        )
