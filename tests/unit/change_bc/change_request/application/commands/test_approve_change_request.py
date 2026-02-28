from unittest.mock import MagicMock

import pytest

from src.change_bc.change_request.application.commands.approve_change_request import (
    ApproveChangeRequestCommand,
    ApproveChangeRequestCommandHandler,
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


class TestApproveChangeRequestCommand:
    def test_approve_pending_approval_schedules(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.status = ChangeStatus.PENDING_APPROVAL
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = ApproveChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            ApproveChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=ADMIN_ID,
                performed_by_role="admin",
            )
        )

        assert change.status == ChangeStatus.SCHEDULED
        assert change.approved_by == ADMIN_ID
        assert change.approved_at is not None
        repo.save.assert_called_once()

    def test_approve_creates_event(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.status = ChangeStatus.PENDING_APPROVAL
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = ApproveChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            ApproveChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=ADMIN_ID,
                performed_by_role="admin",
            )
        )

        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.change_request_id == CHANGE_ID
        assert event.event_type == ChangeEventType.APPROVED
        assert event.actor_id == ADMIN_ID

    def test_approve_with_notes_includes_metadata(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.status = ChangeStatus.PENDING_APPROVAL
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = ApproveChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            ApproveChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=ADMIN_ID,
                performed_by_role="super_admin",
                notes="Looks good",
            )
        )

        event = repo.save_event.call_args[0][0]
        assert event.metadata == {"notes": "Looks good"}

    def test_approve_without_notes_no_metadata(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.status = ChangeStatus.PENDING_APPROVAL
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = ApproveChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            ApproveChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=ADMIN_ID,
                performed_by_role="admin",
            )
        )

        event = repo.save_event.call_args[0][0]
        assert event.metadata is None

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = ApproveChangeRequestCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotFoundError):
            handler.handle(
                ApproveChangeRequestCommand(
                    change_id="nonexistent",
                    company_id=COMPANY_ID,
                    performed_by=ADMIN_ID,
                    performed_by_role="admin",
                )
            )
        repo.save.assert_not_called()

    def test_unauthorized_role_raises(self):
        change = _make_change()
        change.status = ChangeStatus.PENDING_APPROVAL
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = ApproveChangeRequestCommandHandler(change_repo=repo)

        with pytest.raises(UnauthorizedApprovalError):
            handler.handle(
                ApproveChangeRequestCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                    performed_by_role="technician",
                )
            )
        repo.save.assert_not_called()

    def test_approve_from_invalid_status_raises(self):
        change = _make_change()
        change.status = ChangeStatus.DRAFT
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = ApproveChangeRequestCommandHandler(change_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                ApproveChangeRequestCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=ADMIN_ID,
                    performed_by_role="admin",
                )
            )
        repo.save.assert_not_called()
