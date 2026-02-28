from unittest.mock import MagicMock

import pytest

from src.change_bc.change_request.application.commands.create_pir import (
    CreatePIRCommand,
    CreatePIRCommandHandler,
)
from src.change_bc.change_request.domain.entities import ChangeRequest
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
    ChangeType,
    InvalidStatusTransitionError,
    PIROutcome,
)
from src.change_bc.change_request.domain.exceptions import (
    ChangeNotFoundError,
    PIRAlreadyExistsError,
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


def _make_implemented_change(**overrides) -> ChangeRequest:
    change = _make_change(**overrides)
    change.status = ChangeStatus.IMPLEMENTED
    return change


def _base_command(**overrides) -> CreatePIRCommand:
    defaults = dict(
        change_id=CHANGE_ID,
        company_id=COMPANY_ID,
        outcome="successful",
        issues_found=None,
        lessons_learned=None,
        follow_up_actions=None,
        performed_by=ADMIN_ID,
        performed_by_role="admin",
    )
    defaults.update(overrides)
    return CreatePIRCommand(**defaults)


class TestCreatePIRCommand:
    def test_happy_path_creates_pir(self):
        change = _make_implemented_change()
        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_pir_by_change.return_value = None
        handler = CreatePIRCommandHandler(change_repo=repo)

        handler.handle(_base_command())

        repo.save_pir.assert_called_once()
        repo.save_event.assert_called_once()

    def test_change_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = CreatePIRCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotFoundError):
            handler.handle(_base_command(change_id="nonexistent"))

        repo.save_pir.assert_not_called()
        repo.save_event.assert_not_called()

    def test_non_admin_role(self):
        change = _make_implemented_change()
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = CreatePIRCommandHandler(change_repo=repo)

        with pytest.raises(UnauthorizedApprovalError):
            handler.handle(
                _base_command(
                    performed_by=USER_ID,
                    performed_by_role="technician",
                )
            )

        repo.save_pir.assert_not_called()
        repo.save_event.assert_not_called()

    def test_change_not_implemented(self):
        change = _make_change()
        assert change.status == ChangeStatus.DRAFT
        repo = MagicMock()
        repo.find_by_id.return_value = change
        handler = CreatePIRCommandHandler(change_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(_base_command())

        repo.save_pir.assert_not_called()
        repo.save_event.assert_not_called()

    def test_pir_already_exists(self):
        change = _make_implemented_change()
        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_pir_by_change.return_value = MagicMock()  # existing PIR
        handler = CreatePIRCommandHandler(change_repo=repo)

        with pytest.raises(PIRAlreadyExistsError):
            handler.handle(_base_command())

        repo.save_pir.assert_not_called()
        repo.save_event.assert_not_called()

    def test_saves_pir_entity(self):
        change = _make_implemented_change()
        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_pir_by_change.return_value = None
        handler = CreatePIRCommandHandler(change_repo=repo)

        handler.handle(_base_command(outcome="successful"))

        repo.save_pir.assert_called_once()
        pir = repo.save_pir.call_args[0][0]
        assert pir.change_request_id == CHANGE_ID
        assert pir.outcome == PIROutcome.SUCCESSFUL
        assert pir.created_by == ADMIN_ID
        assert len(pir.id) == 26

    def test_creates_pir_added_event(self):
        change = _make_implemented_change()
        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_pir_by_change.return_value = None
        handler = CreatePIRCommandHandler(change_repo=repo)

        handler.handle(_base_command())

        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.change_request_id == CHANGE_ID
        assert event.event_type == ChangeEventType.PIR_ADDED
        assert event.actor_id == ADMIN_ID
        assert event.description == "Post-implementation review added"

    def test_all_fields_passed_through(self):
        change = _make_implemented_change()
        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_pir_by_change.return_value = None
        handler = CreatePIRCommandHandler(change_repo=repo)

        handler.handle(
            _base_command(
                outcome="partial",
                issues_found="Disk space issue",
                lessons_learned="Pre-check storage",
                follow_up_actions="Add monitoring alert",
            )
        )

        pir = repo.save_pir.call_args[0][0]
        assert pir.outcome == PIROutcome.PARTIAL
        assert pir.issues_found == "Disk space issue"
        assert pir.lessons_learned == "Pre-check storage"
        assert pir.follow_up_actions == "Add monitoring alert"
