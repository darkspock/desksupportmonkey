from unittest.mock import MagicMock

import pytest

from src.change_bc.change_request.application.commands.close_change import (
    CloseChangeCommand,
    CloseChangeCommandHandler,
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
    PIRRequiredForEmergencyCloseError,
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


class TestCloseChangeCommand:
    def test_close_implemented_change(self):
        change = _make_change()
        change.status = ChangeStatus.IMPLEMENTED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = CloseChangeCommandHandler(change_repo=repo)

        handler.handle(
            CloseChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=ADMIN_ID,
                performed_by_role="admin",
            )
        )

        assert change.status == ChangeStatus.CLOSED
        assert change.closed_at is not None
        repo.save.assert_called_once()

    def test_close_creates_event(self):
        change = _make_change()
        change.status = ChangeStatus.IMPLEMENTED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = CloseChangeCommandHandler(change_repo=repo)

        handler.handle(
            CloseChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=ADMIN_ID,
                performed_by_role="super_admin",
            )
        )

        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.change_request_id == CHANGE_ID
        assert event.event_type == ChangeEventType.CLOSED
        assert event.actor_id == ADMIN_ID

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = CloseChangeCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotFoundError):
            handler.handle(
                CloseChangeCommand(
                    change_id="nonexistent",
                    company_id=COMPANY_ID,
                    performed_by=ADMIN_ID,
                    performed_by_role="admin",
                )
            )
        repo.save.assert_not_called()

    def test_unauthorized_role_raises(self):
        change = _make_change()
        change.status = ChangeStatus.IMPLEMENTED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = CloseChangeCommandHandler(change_repo=repo)

        with pytest.raises(UnauthorizedApprovalError):
            handler.handle(
                CloseChangeCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=USER_ID,
                    performed_by_role="technician",
                )
            )
        repo.save.assert_not_called()

    def test_close_from_draft_raises(self):
        change = _make_change()
        assert change.status == ChangeStatus.DRAFT
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = CloseChangeCommandHandler(change_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                CloseChangeCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=ADMIN_ID,
                    performed_by_role="admin",
                )
            )
        repo.save.assert_not_called()

    def test_close_already_closed_raises(self):
        change = _make_change()
        change.status = ChangeStatus.CLOSED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = CloseChangeCommandHandler(change_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                CloseChangeCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=ADMIN_ID,
                    performed_by_role="admin",
                )
            )
        repo.save.assert_not_called()


class TestCloseEmergencyPIRGuard:
    def test_emergency_without_pir_raises(self):
        change = _make_change(change_type=ChangeType.EMERGENCY)
        change.status = ChangeStatus.IMPLEMENTED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_pir_by_change.return_value = None
        handler = CloseChangeCommandHandler(change_repo=repo)

        with pytest.raises(PIRRequiredForEmergencyCloseError):
            handler.handle(
                CloseChangeCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    performed_by=ADMIN_ID,
                    performed_by_role="admin",
                )
            )
        repo.save.assert_not_called()

    def test_emergency_with_pir_closes(self):
        change = _make_change(change_type=ChangeType.EMERGENCY)
        change.status = ChangeStatus.IMPLEMENTED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_pir_by_change.return_value = MagicMock()  # PIR exists
        handler = CloseChangeCommandHandler(change_repo=repo)

        handler.handle(
            CloseChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=ADMIN_ID,
                performed_by_role="admin",
            )
        )

        assert change.status == ChangeStatus.CLOSED
        repo.save.assert_called_once()
        repo.save_event.assert_called_once()

    def test_standard_without_pir_closes(self):
        change = _make_change(change_type=ChangeType.STANDARD)
        change.status = ChangeStatus.IMPLEMENTED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = CloseChangeCommandHandler(change_repo=repo)

        handler.handle(
            CloseChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=ADMIN_ID,
                performed_by_role="admin",
            )
        )

        assert change.status == ChangeStatus.CLOSED
        repo.save.assert_called_once()

    def test_normal_without_pir_closes(self):
        change = _make_change(change_type=ChangeType.NORMAL)
        change.status = ChangeStatus.IMPLEMENTED
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = CloseChangeCommandHandler(change_repo=repo)

        handler.handle(
            CloseChangeCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                performed_by=ADMIN_ID,
                performed_by_role="admin",
            )
        )

        assert change.status == ChangeStatus.CLOSED
        repo.save.assert_called_once()
