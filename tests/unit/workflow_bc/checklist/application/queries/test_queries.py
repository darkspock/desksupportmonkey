from unittest.mock import MagicMock

from src.workflow_bc.checklist.application.queries.list_items import (
    ChecklistItemDto,
    ListChecklistItemsQuery,
    ListChecklistItemsQueryHandler,
)
from src.workflow_bc.checklist.domain.entities import RequestChecklistItem


class TestListChecklistItemsQueryHandler:
    def test_list_returns_items(self):
        repo = MagicMock()
        item1 = RequestChecklistItem.create(
            request_id="01REQ", title="Task 1", sort_order=0
        )
        item2 = RequestChecklistItem.create(
            request_id="01REQ", title="Task 2", sort_order=1
        )
        repo.find_by_request.return_value = [item1, item2]

        handler = ListChecklistItemsQueryHandler(repo=repo)
        result = handler.handle(ListChecklistItemsQuery(request_id="01REQ"))

        assert len(result) == 2
        assert isinstance(result[0], ChecklistItemDto)
        assert result[0].title == "Task 1"
        assert result[1].title == "Task 2"

    def test_list_returns_empty(self):
        repo = MagicMock()
        repo.find_by_request.return_value = []

        handler = ListChecklistItemsQueryHandler(repo=repo)
        result = handler.handle(ListChecklistItemsQuery(request_id="01REQ"))

        assert result == []
