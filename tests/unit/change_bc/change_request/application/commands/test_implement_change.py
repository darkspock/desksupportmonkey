from unittest.mock import MagicMock

import pytest

from src.change_bc.change_request.application.commands.implement_change import (
    ImplementChangeCommand,
    ImplementChangeCommandHandler,
)
from src.change_bc.change_request.domain.entities import ChangeRequest
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
    InvalidStatusTransitionError,
)
from src.change_bc.change_request.domain.exceptions import ChangeNotFoundError


CHANGE_ID = "01CHANGE000000000000000001"
COMPANY_ID = "01COMPANY00000000000000001"
USER_ID = "01USER00000000000000000001"


def _make_change(**overrides) -> ChangeRequest:
    defaults = dict(
        id=CHANGE_ID,
        company_id=COMPANY_ID,
        requested_by=USER_ID,
        title="Install security patch",
    )
    defaults.update(overrides)
    return ChangeRequest.create(**defaults)


class TestImplementChangeCommand:
    def test_implement_in_progress_change(self):
        change = _make_change()
        change.status = ChangeStatus.IN_PROGRESS
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = ImplementChangeCommandHandler(change_repo=repo)

        handler.handle(
            ImplementChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
                notes="Patch applied successfully",
            )
        )

        assert change.status == ChangeStatus.IMPLEMENTED
        assert change.implemented_at is not None
        assert change.implementation_notes == "Patch applied successfully"
        repo.save.assert_called_once()

    def test_implement_without_notes(self):
        change = _make_change()
        change.status = ChangeStatus.IN_PROGRESS
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = ImplementChangeCommandHandler(change_repo=repo)

        handler.handle(
            ImplementChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
            )
        )

        assert change.status == ChangeStatus.IMPLEMENTED
        assert change.implementation_notes is None
        repo.save.assert_called_once()

    def test_implement_creates_event(self):
        change = _make_change()
        change.status = ChangeStatus.IN_PROGRESS
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = ImplementChangeCommandHandler(change_repo=repo)

        handler.handle(
            ImplementChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
                notes="Done",
            )
        )

        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.change_request_id == CHANGE_ID
        assert event.event_type == ChangeEventType.IMPLEMENTED
        assert event.actor_id == USER_ID
        assert event.metadata == {"notes": "Done"}

    def test_implement_without_notes_no_metadata(self):
        change = _make_change()
        change.status = ChangeStatus.IN_PROGRESS
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = ImplementChangeCommandHandler(change_repo=repo)

        handler.handle(
            ImplementChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
            )
        )

        event = repo.save_event.call_args[0][0]
        assert event.metadata is None

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = ImplementChangeCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotFoundError):
            handler.handle(
                ImplementChangeCommand(
                    change_id="nonexistent",
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                )
            )
        repo.save.assert_not_called()

    def test_implement_from_draft_raises(self):
        change = _make_change()
        assert change.status == ChangeStatus.DRAFT
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = ImplementChangeCommandHandler(change_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                ImplementChangeCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                )
            )
        repo.save.assert_not_called()
