from unittest.mock import MagicMock

import pytest

from src.request_bc.request.application.queries.get_request import (
    GetRequestQuery,
    GetRequestQueryHandler,
    RequestNotFoundError,
)
from src.request_bc.request.application.queries.list_requests import (
    ListRequestsQuery,
    ListRequestsQueryHandler,
)
from src.request_bc.request.application.queries.list_comments import (
    ListCommentsQuery,
    ListCommentsQueryHandler,
    RequestNotFoundError as CommentsNotFoundError,
)
from src.request_bc.request.application.queries.list_notes import (
    ListNotesQuery,
    ListNotesQueryHandler,
    RequestNotFoundError as NotesNotFoundError,
)
from src.request_bc.request.application.queries.my_requests import (
    MyRequestsQuery,
    MyRequestsQueryHandler,
)
from src.request_bc.request.domain.entities import RequestComment, RequestNote, ServiceRequest
from src.request_bc.request.domain.enums import RequestType


def _make_request(**overrides):
    defaults = dict(
        company_id="comp1",
        created_by="user1",
        type=RequestType.INCIDENT,
        title="Test request",
        description="Test description",
    )
    defaults.update(overrides)
    return ServiceRequest.create(**defaults)


class TestListRequestsQuery:
    def test_returns_paginated(self):
        requests = [_make_request(title=f"Req {i}") for i in range(3)]
        repo = MagicMock()
        repo.find_all.return_value = (requests, 3)
        handler = ListRequestsQueryHandler(request_repo=repo)

        result, total = handler.handle(
            ListRequestsQuery(company_id="comp1", page=1, page_size=20)
        )

        assert len(result) == 3
        assert total == 3
        repo.find_all.assert_called_once_with(
            company_id="comp1", page=1, page_size=20,
            search=None, status=None, type=None,
            priority=None, assigned_to=None, subtype=None,
        )

    def test_passes_filter_params(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)
        handler = ListRequestsQueryHandler(request_repo=repo)

        handler.handle(
            ListRequestsQuery(
                company_id="comp1",
                search="laptop",
                status="submitted",
                type="incident",
                priority="high",
                assigned_to="tech1",
            )
        )

        call_kwargs = repo.find_all.call_args.kwargs
        assert call_kwargs["search"] == "laptop"
        assert call_kwargs["status"] == "submitted"
        assert call_kwargs["type"] == "incident"
        assert call_kwargs["priority"] == "high"
        assert call_kwargs["assigned_to"] == "tech1"


class TestGetRequestQuery:
    def test_success_with_comment_count(self):
        request = _make_request()
        repo = MagicMock()
        repo.find_by_id.return_value = request
        repo.count_comments.return_value = 5
        handler = GetRequestQueryHandler(request_repo=repo)

        detail = handler.handle(
            GetRequestQuery(request_id=request.id, company_id="comp1")
        )

        assert detail.request.id == request.id
        assert detail.comment_count == 5
        repo.find_by_id.assert_called_once_with(request.id, "comp1")
        repo.count_comments.assert_called_once_with(request.id)

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetRequestQueryHandler(request_repo=repo)

        with pytest.raises(RequestNotFoundError):
            handler.handle(
                GetRequestQuery(request_id="bad", company_id="comp1")
            )


class TestListCommentsQuery:
    def test_success(self):
        request = _make_request()
        comments = [
            RequestComment.create(request_id=request.id, author_id="user1", body="Comment 1"),
            RequestComment.create(request_id=request.id, author_id="tech1", body="Comment 2"),
        ]
        repo = MagicMock()
        repo.find_by_id.return_value = request
        repo.find_comments.return_value = comments
        handler = ListCommentsQueryHandler(request_repo=repo)

        result = handler.handle(
            ListCommentsQuery(request_id=request.id, company_id="comp1")
        )

        assert len(result) == 2
        assert result[0].body == "Comment 1"
        assert result[1].body == "Comment 2"

    def test_request_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = ListCommentsQueryHandler(request_repo=repo)

        with pytest.raises(CommentsNotFoundError):
            handler.handle(
                ListCommentsQuery(request_id="bad", company_id="comp1")
            )


class TestListNotesQuery:
    def test_success(self):
        request = _make_request()
        notes = [
            RequestNote.create(request_id=request.id, author_id="tech1", body="Note 1"),
        ]
        repo = MagicMock()
        repo.find_by_id.return_value = request
        repo.find_notes.return_value = notes
        handler = ListNotesQueryHandler(request_repo=repo)

        result = handler.handle(
            ListNotesQuery(request_id=request.id, company_id="comp1")
        )

        assert len(result) == 1
        assert result[0].body == "Note 1"

    def test_request_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = ListNotesQueryHandler(request_repo=repo)

        with pytest.raises(NotesNotFoundError):
            handler.handle(
                ListNotesQuery(request_id="bad", company_id="comp1")
            )


class TestMyRequestsQuery:
    def test_returns_paginated(self):
        requests = [_make_request(title=f"My Req {i}") for i in range(2)]
        repo = MagicMock()
        repo.find_by_created_by.return_value = (requests, 2)
        handler = MyRequestsQueryHandler(request_repo=repo)

        result, total = handler.handle(
            MyRequestsQuery(user_id="user1", company_id="comp1", page=1, page_size=20)
        )

        assert len(result) == 2
        assert total == 2
        repo.find_by_created_by.assert_called_once_with(
            user_id="user1", company_id="comp1",
            page=1, page_size=20, status=None, subtype=None,
        )

    def test_passes_status_filter(self):
        repo = MagicMock()
        repo.find_by_created_by.return_value = ([], 0)
        handler = MyRequestsQueryHandler(request_repo=repo)

        handler.handle(
            MyRequestsQuery(
                user_id="user1", company_id="comp1", status="submitted"
            )
        )

        call_kwargs = repo.find_by_created_by.call_args.kwargs
        assert call_kwargs["status"] == "submitted"
