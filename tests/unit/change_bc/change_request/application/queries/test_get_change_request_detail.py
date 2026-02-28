from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.change_bc.change_request.application.queries.get_change_request_detail import (
    ChangeEventDto,
    ChangeRequestDetailDto,
    GetChangeRequestDetailQuery,
    GetChangeRequestDetailQueryHandler,
)
from src.change_bc.change_request.domain.entities import ChangeEvent, ChangeRequest
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
    ChangeType,
)


CHANGE_ID = "01CHANGE000000000000000001"
COMPANY_ID = "01COMPANY00000000000000001"
USER_ID = "01USER00000000000000000001"
ADMIN_ID = "01ADMIN00000000000000000001"
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


def _make_event(**overrides) -> ChangeEvent:
    defaults = dict(
        change_request_id=CHANGE_ID,
        event_type=ChangeEventType.CREATED,
        description="Change request created",
        actor_id=USER_ID,
    )
    defaults.update(overrides)
    return ChangeEvent.create(**defaults)


class TestGetChangeRequestDetailQuery:
    def test_returns_detail_dto(self):
        change = _make_change()
        change.description = "Apply security updates"
        change.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        event = _make_event()
        event.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_events.return_value = [event]
        handler = GetChangeRequestDetailQueryHandler(change_repo=repo)

        dto = handler.handle(
            GetChangeRequestDetailQuery(
                change_id=CHANGE_ID, company_id=COMPANY_ID
            )
        )

        assert dto is not None
        assert dto.id == CHANGE_ID
        assert dto.company_id == COMPANY_ID
        assert dto.title == "Install security patch"
        assert dto.description == "Apply security updates"
        assert dto.change_type == ChangeType.STANDARD.value
        assert dto.status == ChangeStatus.DRAFT.value

    def test_not_found_returns_none(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetChangeRequestDetailQueryHandler(change_repo=repo)

        result = handler.handle(
            GetChangeRequestDetailQuery(
                change_id="nonexistent", company_id=COMPANY_ID
            )
        )

        assert result is None
        repo.find_events.assert_not_called()

    def test_timeline_events_included(self):
        change = _make_change()
        event1 = _make_event(
            event_type=ChangeEventType.CREATED,
            description="Created",
        )
        event1.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        event2 = _make_event(
            event_type=ChangeEventType.SUBMITTED,
            description="Submitted",
            actor_id=ADMIN_ID,
        )
        event2.created_at = datetime(2026, 1, 2, tzinfo=timezone.utc)

        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_events.return_value = [event1, event2]
        handler = GetChangeRequestDetailQueryHandler(change_repo=repo)

        dto = handler.handle(
            GetChangeRequestDetailQuery(
                change_id=CHANGE_ID, company_id=COMPANY_ID
            )
        )

        assert len(dto.timeline) == 2
        assert dto.timeline[0].event_type == ChangeEventType.CREATED.value
        assert dto.timeline[0].description == "Created"
        assert dto.timeline[1].event_type == ChangeEventType.SUBMITTED.value
        assert dto.timeline[1].actor_id == ADMIN_ID

    def test_find_events_called_with_change_id(self):
        change = _make_change()
        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_events.return_value = []
        handler = GetChangeRequestDetailQueryHandler(change_repo=repo)

        handler.handle(
            GetChangeRequestDetailQuery(
                change_id=CHANGE_ID, company_id=COMPANY_ID
            )
        )

        repo.find_events.assert_called_once_with(CHANGE_ID)

    def test_user_name_resolver_called_with_all_user_ids(self):
        change = _make_change()
        change.assigned_to = ASSIGNEE_ID
        change.approved_by = ADMIN_ID
        event = _make_event(actor_id="01ACTOR00000000000000000001")

        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_events.return_value = [event]

        resolver = MagicMock(
            return_value={
                USER_ID: "John Doe",
                ASSIGNEE_ID: "Jane Tech",
                ADMIN_ID: "Admin User",
                "01ACTOR00000000000000000001": "Actor User",
            }
        )
        handler = GetChangeRequestDetailQueryHandler(
            change_repo=repo, user_name_resolver=resolver
        )

        dto = handler.handle(
            GetChangeRequestDetailQuery(
                change_id=CHANGE_ID, company_id=COMPANY_ID
            )
        )

        # First call resolves main user IDs; second may resolve PIR created_by
        assert resolver.call_count >= 1
        called_ids = set(resolver.call_args_list[0][0][0])
        assert USER_ID in called_ids
        assert ASSIGNEE_ID in called_ids
        assert ADMIN_ID in called_ids
        assert "01ACTOR00000000000000000001" in called_ids

    def test_name_resolver_populates_names(self):
        change = _make_change()
        change.assigned_to = ASSIGNEE_ID
        change.approved_by = ADMIN_ID
        change.rejected_by = None
        event = _make_event()

        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_events.return_value = [event]

        resolver = MagicMock(
            return_value={
                USER_ID: "John Doe",
                ASSIGNEE_ID: "Jane Tech",
                ADMIN_ID: "Admin User",
            }
        )
        handler = GetChangeRequestDetailQueryHandler(
            change_repo=repo, user_name_resolver=resolver
        )

        dto = handler.handle(
            GetChangeRequestDetailQuery(
                change_id=CHANGE_ID, company_id=COMPANY_ID
            )
        )

        assert dto.requested_by_name == "John Doe"
        assert dto.assigned_to_name == "Jane Tech"
        assert dto.approved_by_name == "Admin User"
        assert dto.rejected_by_name is None

    def test_no_resolver_names_are_none(self):
        change = _make_change()
        change.assigned_to = ASSIGNEE_ID
        event = _make_event()

        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_events.return_value = [event]
        handler = GetChangeRequestDetailQueryHandler(change_repo=repo)

        dto = handler.handle(
            GetChangeRequestDetailQuery(
                change_id=CHANGE_ID, company_id=COMPANY_ID
            )
        )

        assert dto.requested_by_name is None
        assert dto.assigned_to_name is None

    def test_timeline_event_actor_names_resolved(self):
        change = _make_change()
        event = _make_event(actor_id=ADMIN_ID)

        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_events.return_value = [event]

        resolver = MagicMock(
            return_value={
                USER_ID: "John Doe",
                ADMIN_ID: "Admin User",
            }
        )
        handler = GetChangeRequestDetailQueryHandler(
            change_repo=repo, user_name_resolver=resolver
        )

        dto = handler.handle(
            GetChangeRequestDetailQuery(
                change_id=CHANGE_ID, company_id=COMPANY_ID
            )
        )

        assert dto.timeline[0].actor_name == "Admin User"

    def test_event_metadata_included(self):
        change = _make_change()
        event = _make_event(metadata={"auto_approved": True})

        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_events.return_value = [event]
        handler = GetChangeRequestDetailQueryHandler(change_repo=repo)

        dto = handler.handle(
            GetChangeRequestDetailQuery(
                change_id=CHANGE_ID, company_id=COMPANY_ID
            )
        )

        assert dto.timeline[0].metadata == {"auto_approved": True}

    def test_approved_change_fields_populated(self):
        change = _make_change()
        change.status = ChangeStatus.SCHEDULED
        change.approved_by = ADMIN_ID
        change.approved_at = datetime(2026, 1, 5, tzinfo=timezone.utc)

        repo = MagicMock()
        repo.find_by_id.return_value = change
        repo.find_events.return_value = []
        handler = GetChangeRequestDetailQueryHandler(change_repo=repo)

        dto = handler.handle(
            GetChangeRequestDetailQuery(
                change_id=CHANGE_ID, company_id=COMPANY_ID
            )
        )

        assert dto.approved_by == ADMIN_ID
        assert dto.approved_at == datetime(2026, 1, 5, tzinfo=timezone.utc)
        assert dto.status == ChangeStatus.SCHEDULED.value
