from unittest.mock import MagicMock

import pytest

from src.request_bc.request.application.commands.add_note import (
    AddNoteCommand,
    AddNoteCommandHandler,
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


class TestAddNoteCommand:
    def test_success(self):
        request = _make_request()
        repo = MagicMock()
        repo.find_by_id.return_value = request
        repo.save_note.side_effect = lambda n: n
        handler = AddNoteCommandHandler(request_repo=repo)

        result = handler.handle(
            AddNoteCommand(
                request_id=request.id,
                company_id="comp1",
                author_id="tech1",
                body="Internal note",
            )
        )

        assert result.body == "Internal note"
        assert result.author_id == "tech1"
        assert repo.save_note.call_count == 1
        assert repo.save_event.call_count == 1
        event = repo.save_event.call_args[0][0]
        assert event.event_type == "note_added"

    def test_request_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = AddNoteCommandHandler(request_repo=repo)

        with pytest.raises(RequestNotFoundError):
            handler.handle(
                AddNoteCommand(
                    request_id="bad",
                    company_id="comp1",
                    author_id="tech1",
                    body="Note",
                )
            )

    def test_empty_body_raises(self):
        request = _make_request()
        repo = MagicMock()
        repo.find_by_id.return_value = request
        handler = AddNoteCommandHandler(request_repo=repo)

        with pytest.raises(ValueError, match="Note body is required"):
            handler.handle(
                AddNoteCommand(
                    request_id=request.id,
                    company_id="comp1",
                    author_id="tech1",
                    body="",
                )
            )
