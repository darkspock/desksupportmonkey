from unittest.mock import MagicMock

import pytest

from src.request_bc.request.application.commands.add_comment import (
    AddCommentCommand,
    AddCommentCommandHandler,
    RequestNotFoundError,
)
from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.domain.enums import RequestType


def _make_request():
    return ServiceRequest.create(
        company_id="comp1",
        created_by="user1",
        type=RequestType.INCIDENT,
        title="Test",
        description="Test desc",
    )


class TestAddCommentCommand:
    def test_success(self):
        request = _make_request()
        repo = MagicMock()
        repo.find_by_id.return_value = request
        repo.save_comment.side_effect = lambda c: c
        handler = AddCommentCommandHandler(request_repo=repo)

        handler.handle(
            AddCommentCommand(
                request_id=request.id,
                company_id="comp1",
                author_id="user1",
                body="This is a comment",
            )
        )

        assert repo.save_comment.call_count == 1
        assert repo.save_event.call_count == 1
        event = repo.save_event.call_args[0][0]
        assert event.event_type == "comment_added"
        assert event.data["author_id"] == "user1"

    def test_request_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = AddCommentCommandHandler(request_repo=repo)

        with pytest.raises(RequestNotFoundError):
            handler.handle(
                AddCommentCommand(
                    request_id="bad",
                    company_id="comp1",
                    author_id="user1",
                    body="Comment",
                )
            )

    def test_empty_body_raises(self):
        request = _make_request()
        repo = MagicMock()
        repo.find_by_id.return_value = request
        handler = AddCommentCommandHandler(request_repo=repo)

        with pytest.raises(ValueError, match="Comment body is required"):
            handler.handle(
                AddCommentCommand(
                    request_id=request.id,
                    company_id="comp1",
                    author_id="user1",
                    body="",
                )
            )
