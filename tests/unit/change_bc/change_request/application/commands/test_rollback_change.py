from unittest.mock import MagicMock

import pytest

from src.change_bc.change_request.application.commands.rollback_change import (
    RollbackChangeCommand,
    RollbackChangeCommandHandler,
)
from src.change_bc.change_request.domain.entities import ChangeRequest
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
    InvalidStatusTransitionError,
)
from src.change_bc.change_request.domain.exceptions import (
    ChangeNotFoundError,
    RollbackReasonRequiredError,
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


class TestRollbackChangeCommand:
    def test_rollback_in_progress_change(self):
        change = _make_change()
        change.status = ChangeStatus.IN_PROGRESS
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = RollbackChangeCommandHandler(change_repo=repo)

        handler.handle(
            RollbackChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
                reason="Critical error found",
            )
        )

        assert change.status == ChangeStatus.ROLLED_BACK
        assert change.rolled_back_at is not None
        assert change.rollback_reason == "Critical error found"
        repo.save.assert_called_once()

    def test_rollback_implemented_change(self):
        change = _make_change()
        change.status = ChangeStatus.IMPLEMENTED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = RollbackChangeCommandHandler(change_repo=repo)

        handler.handle(
            RollbackChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
                reason="Performance degradation",
            )
        )

        assert change.status == ChangeStatus.ROLLED_BACK
        repo.save.assert_called_once()

    def test_rollback_creates_event(self):
        change = _make_change()
        change.status = ChangeStatus.IN_PROGRESS
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = RollbackChangeCommandHandler(change_repo=repo)

        handler.handle(
            RollbackChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=USER_ID,
                reason="Critical error found",
            )
        )

        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.change_request_id == CHANGE_ID
        assert event.event_type == ChangeEventType.ROLLED_BACK
        assert event.actor_id == USER_ID
        assert event.metadata == {"reason": "Critical error found"}

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = RollbackChangeCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotFoundError):
            handler.handle(
                RollbackChangeCommand(
                    change_id="nonexistent",
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                    reason="Some reason",
                )
            )
        repo.save.assert_not_called()

    def test_empty_reason_raises(self):
        change = _make_change()
        change.status = ChangeStatus.IN_PROGRESS
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = RollbackChangeCommandHandler(change_repo=repo)

        with pytest.raises(RollbackReasonRequiredError):
            handler.handle(
                RollbackChangeCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                    reason="   ",
                )
            )
        repo.save.assert_not_called()

    def test_rollback_from_draft_raises(self):
        change = _make_change()
        assert change.status == ChangeStatus.DRAFT
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = RollbackChangeCommandHandler(change_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                RollbackChangeCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                    reason="Want to rollback",
                )
            )
        repo.save.assert_not_called()
