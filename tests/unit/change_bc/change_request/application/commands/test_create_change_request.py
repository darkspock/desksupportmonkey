from unittest.mock import MagicMock

import pytest

from src.change_bc.change_request.application.commands.create_change_request import (
    CreateChangeRequestCommand,
    CreateChangeRequestCommandHandler,
)
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
    ChangeType,
)


CHANGE_ID = "01CHANGE000000000000000001"
COMPANY_ID = "01COMPANY00000000000000001"
USER_ID = "01USER00000000000000000001"


class TestCreateChangeRequestCommand:
    def test_creates_change_and_saves(self):
        repo = MagicMock()
        handler = CreateChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            CreateChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                requested_by=USER_ID,
                title="Install security patch",
            )
        )

        repo.save.assert_called_once()
        change = repo.save.call_args[0][0]
        assert change.id == CHANGE_ID
        assert change.company_id == COMPANY_ID
        assert change.requested_by == USER_ID
        assert change.title == "Install security patch"
        assert change.status == ChangeStatus.DRAFT
        assert change.change_type == ChangeType.STANDARD

    def test_creates_event(self):
        repo = MagicMock()
        handler = CreateChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            CreateChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                requested_by=USER_ID,
                title="Install security patch",
            )
        )

        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.change_request_id == CHANGE_ID
        assert event.event_type == ChangeEventType.CREATED
        assert event.actor_id == USER_ID

    def test_creates_with_change_type(self):
        repo = MagicMock()
        handler = CreateChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            CreateChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                requested_by=USER_ID,
                title="Emergency fix",
                change_type="emergency",
            )
        )

        change = repo.save.call_args[0][0]
        assert change.change_type == ChangeType.EMERGENCY

    def test_creates_with_planned_date(self):
        from datetime import datetime, timezone

        planned = datetime(2026, 3, 15, tzinfo=timezone.utc)
        repo = MagicMock()
        handler = CreateChangeRequestCommandHandler(change_repo=repo)

        handler.handle(
            CreateChangeRequestCommand(
                change_id=CHANGE_ID,
                company_id=COMPANY_ID,
                requested_by=USER_ID,
                title="Scheduled maintenance",
                planned_date=planned,
            )
        )

        change = repo.save.call_args[0][0]
        assert change.planned_date == planned

    def test_empty_title_raises(self):
        repo = MagicMock()
        handler = CreateChangeRequestCommandHandler(change_repo=repo)

        with pytest.raises(ValueError, match="Title is required"):
            handler.handle(
                CreateChangeRequestCommand(
                    change_id=CHANGE_ID,
                    company_id=COMPANY_ID,
                    requested_by=USER_ID,
                    title="   ",
                )
            )
        repo.save.assert_not_called()
