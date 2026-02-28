from unittest.mock import MagicMock

import pytest

from src.change_bc.change_request.application.commands.update_change_request import (
    UpdateChangeRequestCommand,
    UpdateChangeRequestCommandHandler,
)
from src.change_bc.change_request.domain.entities import ChangeRequest
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
    ChangeType,
)
from src.change_bc.change_request.domain.exceptions import (
    ChangeNotEditableError,
    ChangeNotFoundError,
)


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


class TestUpdateChangeRequestCommand:
    def test_updates_title_and_saves(self):
        change = _make_change()
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = UpdateChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            UpdateChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
                title="Updated title",
            )
        )

        assert change.title == "Updated title"
        repo.save.assert_called_once()

    def test_updates_description_and_rollback_plan(self):
        change = _make_change()
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = UpdateChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            UpdateChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
                description="New description",
                rollback_plan="Revert deployment",
            )
        )

        assert change.description == "New description"
        assert change.rollback_plan == "Revert deployment"
        repo.save.assert_called_once()

    def test_creates_event(self):
        change = _make_change()
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = UpdateChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            UpdateChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
                title="New title",
            )
        )

        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.change_request_id == CHANGE_ID
        assert event.event_type == ChangeEventType.UPDATED
        assert event.actor_id == USER_ID

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = UpdateChangeRequestCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotFoundError):
            handler.handle(
                UpdateChangeRequestCommand(
                    change_id="nonexistent",
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                    title="New title",
                )
            )
        repo.save.assert_not_called()

    def test_not_editable_in_scheduled_status_raises(self):
        change = _make_change()
        change.status = ChangeStatus.SCHEDULED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = UpdateChangeRequestCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotEditableError):
            handler.handle(
                UpdateChangeRequestCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                    title="New title",
                )
            )
        repo.save.assert_not_called()

    def test_editable_in_pending_approval_status(self):
        change = _make_change()
        change.status = ChangeStatus.PENDING_APPROVAL
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = UpdateChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            UpdateChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
                title="Updated in pending",
            )
        )

        assert change.title == "Updated in pending"
        repo.save.assert_called_once()
