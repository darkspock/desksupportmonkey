from unittest.mock import MagicMock

import pytest

from src.change_bc.change_request.application.commands.assign_change import (
    AssignChangeCommand,
    AssignChangeCommandHandler,
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
ASSIGNEE_ID = "01ASSIGNEE0000000000000001"


def _make_change(**overrides) -> ChangeRequest:
    defaults = dict(
        id=CHANGE_ID,
        company_id=COMPANY_ID,
        requested_by=USER_ID,
        title="Install security patch",
    )
    defaults.update(overrides)
    return ChangeRequest.create(**defaults)


class TestAssignChangeCommand:
    def test_assign_draft_change(self):
        change = _make_change()
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = AssignChangeCommandHandler(change_repo=repo)

        handler.handle(
            AssignChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
                assigned_to=ASSIGNEE_ID,
            )
        )

        assert change.assigned_to == ASSIGNEE_ID
        repo.save.assert_called_once()

    def test_assign_scheduled_change(self):
        change = _make_change()
        change.status = ChangeStatus.SCHEDULED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = AssignChangeCommandHandler(change_repo=repo)

        handler.handle(
            AssignChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
                assigned_to=ASSIGNEE_ID,
            )
        )

        assert change.assigned_to == ASSIGNEE_ID
        repo.save.assert_called_once()

    def test_assign_creates_event(self):
        change = _make_change()
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = AssignChangeCommandHandler(change_repo=repo)

        handler.handle(
            AssignChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
                assigned_to=ASSIGNEE_ID,
            )
        )

        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.change_request_id == CHANGE_ID
        assert event.event_type == ChangeEventType.ASSIGNED
        assert event.actor_id == USER_ID
        assert event.metadata == {"assigned_to": ASSIGNEE_ID}

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = AssignChangeCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotFoundError):
            handler.handle(
                AssignChangeCommand(
                    change_id="nonexistent",
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                    assigned_to=ASSIGNEE_ID,
                )
            )
        repo.save.assert_not_called()

    def test_assign_closed_raises(self):
        change = _make_change()
        change.status = ChangeStatus.CLOSED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = AssignChangeCommandHandler(change_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                AssignChangeCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                    assigned_to=ASSIGNEE_ID,
                )
            )
        repo.save.assert_not_called()

    def test_assign_rejected_raises(self):
        change = _make_change()
        change.status = ChangeStatus.REJECTED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = AssignChangeCommandHandler(change_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                AssignChangeCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                    assigned_to=ASSIGNEE_ID,
                )
            )
        repo.save.assert_not_called()

    def test_assign_rolled_back_raises(self):
        change = _make_change()
        change.status = ChangeStatus.ROLLED_BACK
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = AssignChangeCommandHandler(change_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                AssignChangeCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                    assigned_to=ASSIGNEE_ID,
                )
            )
        repo.save.assert_not_called()
