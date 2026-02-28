from unittest.mock import MagicMock

import pytest

from src.change_bc.change_request.application.commands.reject_change_request import (
    RejectChangeRequestCommand,
    RejectChangeRequestCommandHandler,
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
    RejectionReasonRequiredError,
    UnauthorizedApprovalError,
)


CHANGE_ID = "01CHANGE000000000000000001"
COMPANY_ID = "01COMPANY00000000000000001"
USER_ID = "01USER00000000000000000001"
ADMIN_ID = "01ADMIN00000000000000000001"


def _make_change(**overrides) -> ChangeRequest:
    defaults = dict(
        id=CHANGE_ID,
        company_id=COMPANY_ID,
        requested_by=USER_ID,
        title="Install security patch",
    )
    defaults.update(overrides)
    return ChangeRequest.create(**defaults)


class TestRejectChangeRequestCommand:
    def test_reject_pending_approval_succeeds(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.status = ChangeStatus.PENDING_APPROVAL
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = RejectChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            RejectChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=ADMIN_ID,
                performed_by_role="admin",
                reason="Insufficient justification",
            )
        )

        assert change.status == ChangeStatus.REJECTED
        assert change.rejected_by == ADMIN_ID
        assert change.rejected_at is not None
        assert change.rejection_reason == "Insufficient justification"
        repo.save.assert_called_once()

    def test_reject_creates_event(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.status = ChangeStatus.PENDING_APPROVAL
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = RejectChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            RejectChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=ADMIN_ID,
                performed_by_role="super_admin",
                reason="Too risky",
            )
        )

        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.change_request_id == CHANGE_ID
        assert event.event_type == ChangeEventType.REJECTED
        assert event.actor_id == ADMIN_ID
        assert event.metadata == {"reason": "Too risky"}

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = RejectChangeRequestCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotFoundError):
            handler.handle(
                RejectChangeRequestCommand(
                    change_id="nonexistent",
                    company_id=COMPANY_ID,
                    performed_by=ADMIN_ID,
                    performed_by_role="admin",
                    reason="Some reason",
                )
            )
        repo.save.assert_not_called()

    def test_unauthorized_role_raises(self):
        change = _make_change()
        change.status = ChangeStatus.PENDING_APPROVAL
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = RejectChangeRequestCommandHandler(change_repo=repo)

        with pytest.raises(UnauthorizedApprovalError):
            handler.handle(
                RejectChangeRequestCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                    performed_by_role="technician",
                    reason="Some reason",
                )
            )
        repo.save.assert_not_called()

    def test_empty_reason_raises(self):
        change = _make_change()
        change.status = ChangeStatus.PENDING_APPROVAL
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = RejectChangeRequestCommandHandler(change_repo=repo)

        with pytest.raises(RejectionReasonRequiredError):
            handler.handle(
                RejectChangeRequestCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=ADMIN_ID,
                    performed_by_role="admin",
                    reason="   ",
                )
            )
        repo.save.assert_not_called()

    def test_reject_from_invalid_status_raises(self):
        change = _make_change()
        change.status = ChangeStatus.DRAFT
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = RejectChangeRequestCommandHandler(change_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                RejectChangeRequestCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=ADMIN_ID,
                    performed_by_role="admin",
                    reason="Not needed",
                )
            )
        repo.save.assert_not_called()
