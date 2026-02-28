from unittest.mock import MagicMock

import pytest

from src.change_bc.change_request.application.commands.submit_change_request import (
    SubmitChangeRequestCommand,
    SubmitChangeRequestCommandHandler,
)
from src.change_bc.change_request.domain.entities import ChangeRequest
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
    ChangeType,
    InvalidStatusTransitionError,
)
from src.change_bc.change_request.domain.exceptions import (
    ChangeNotFoundError,
    RollbackPlanRequiredError,
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


class TestSubmitChangeRequestCommand:
    def test_submit_standard_auto_scheduled(self):
        change = _make_change(change_type=ChangeType.STANDARD)
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = SubmitChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            SubmitChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
            )
        )

        assert change.status == ChangeStatus.SCHEDULED
        repo.save.assert_called_once()

    def test_submit_standard_event_with_auto_approved_true(self):
        change = _make_change(change_type=ChangeType.STANDARD)
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = SubmitChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            SubmitChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
            )
        )

        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.event_type == ChangeEventType.SUBMITTED
        assert event.actor_id == USER_ID
        assert event.metadata == {"auto_approved": True}

    def test_submit_normal_goes_to_pending_approval(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.rollback_plan = "Revert deployment"
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = SubmitChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            SubmitChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
            )
        )

        assert change.status == ChangeStatus.PENDING_APPROVAL
        repo.save.assert_called_once()

    def test_submit_normal_event_with_auto_approved_false(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.rollback_plan = "Revert deployment"
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = SubmitChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            SubmitChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
            )
        )

        event = repo.save_event.call_args[0][0]
        assert event.metadata == {"auto_approved": False}

    def test_submit_normal_without_rollback_plan_raises(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = SubmitChangeRequestCommandHandler(change_repo=repo)

        with pytest.raises(RollbackPlanRequiredError):
            handler.handle(
                SubmitChangeRequestCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                )
            )
        repo.save.assert_not_called()

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = SubmitChangeRequestCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotFoundError):
            handler.handle(
                SubmitChangeRequestCommand(
                    change_id="nonexistent",
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                )
            )
        repo.save.assert_not_called()

    def test_submit_from_invalid_status_raises(self):
        change = _make_change()
        change.status = ChangeStatus.CLOSED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = SubmitChangeRequestCommandHandler(change_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                SubmitChangeRequestCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                )
            )
        repo.save.assert_not_called()
