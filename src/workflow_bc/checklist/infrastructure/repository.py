from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.workflow_bc.checklist.domain.entities import RequestChecklistItem
from src.workflow_bc.checklist.domain.repository import ChecklistItemRepositoryInterface
from src.workflow_bc.checklist.infrastructure.models import RequestChecklistItemModel


class ChecklistItemRepository(ChecklistItemRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def _model_to_entity(self, m: RequestChecklistItemModel) -> RequestChecklistItem:
        return RequestChecklistItem(
            id=m.id,
            request_id=m.request_id,
            require_all_complete=m.require_all_complete,
            title=m.title,
            description=m.description,
            assignee_id=m.assignee_id,
            is_required=m.is_required,
            is_completed=m.is_completed,
            completed_by=m.completed_by,
            completed_at=m.completed_at,
            sort_order=m.sort_order,
            created_at=m.created_at,
        )

    def save(self, item: RequestChecklistItem) -> None:
        existing = self.session.execute(
            select(RequestChecklistItemModel).where(
                RequestChecklistItemModel.id == item.id
            )
        ).scalar_one_or_none()

        if existing:
            existing.title = item.title
            existing.description = item.description
            existing.assignee_id = item.assignee_id
            existing.is_required = item.is_required
            existing.is_completed = item.is_completed
            existing.completed_by = item.completed_by
            existing.completed_at = item.completed_at
            existing.sort_order = item.sort_order
        else:
            self.session.add(
                RequestChecklistItemModel(
                    id=item.id,
                    request_id=item.request_id,
                    require_all_complete=item.require_all_complete,
                    title=item.title,
                    description=item.description,
                    assignee_id=item.assignee_id,
                    is_required=item.is_required,
                    is_completed=item.is_completed,
                    completed_by=item.completed_by,
                    completed_at=item.completed_at,
                    sort_order=item.sort_order,
                    created_at=item.created_at,
                )
            )
        self.session.flush()

    def save_all(self, items: list[RequestChecklistItem]) -> None:
        for item in items:
            self.save(item)

    def find_by_id(self, item_id: str) -> Optional[RequestChecklistItem]:
        m = self.session.execute(
            select(RequestChecklistItemModel).where(
                RequestChecklistItemModel.id == item_id
            )
        ).scalar_one_or_none()
        return self._model_to_entity(m) if m else None

    def find_by_request(self, request_id: str) -> list[RequestChecklistItem]:
        models = (
            self.session.execute(
                select(RequestChecklistItemModel)
                .where(RequestChecklistItemModel.request_id == request_id)
                .order_by(RequestChecklistItemModel.sort_order)
            )
            .scalars()
            .all()
        )
        return [self._model_to_entity(m) for m in models]

    def delete(self, item_id: str) -> None:
        model = self.session.execute(
            select(RequestChecklistItemModel).where(
                RequestChecklistItemModel.id == item_id
            )
        ).scalar_one_or_none()
        if model:
            self.session.delete(model)
            self.session.flush()
