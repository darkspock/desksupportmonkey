from unittest.mock import MagicMock

from src.notification_bc.notification.application.services.target_resolver import TargetResolver
from src.notification_bc.notification.domain.enums import EventType
from src.notification_bc.notification.domain.events import DomainEvent


def _make_event(event_type, actor_id="actor1", **payload_overrides):
    payload = {"request_id": "req1", "created_by": "creator1", "assigned_to": "tech1"}
    payload.update(payload_overrides)
    return DomainEvent(
        event_type=event_type,
        company_id="comp1",
        actor_id=actor_id,
        payload=payload,
        title="Test",
        body="Test body",
    )


class TestTargetResolver:
    def test_request_created_targets_all_technicians(self):
        repo = MagicMock()
        repo.find_technician_ids_by_company.return_value = ["tech1", "tech2", "tech3"]
        resolver = TargetResolver(user_repo=repo)

        event = _make_event(EventType.REQUEST_CREATED, actor_id="creator1")
        targets = resolver.resolve(event)

        assert set(targets) == {"tech1", "tech2", "tech3"}
        repo.find_technician_ids_by_company.assert_called_once_with("comp1")

    def test_request_created_excludes_actor(self):
        repo = MagicMock()
        repo.find_technician_ids_by_company.return_value = ["tech1", "creator1"]
        resolver = TargetResolver(user_repo=repo)

        event = _make_event(EventType.REQUEST_CREATED, actor_id="creator1")
        targets = resolver.resolve(event)

        assert targets == ["tech1"]

    def test_status_changed_targets_creator_and_assigned(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        event = _make_event(EventType.REQUEST_STATUS_CHANGED, actor_id="actor1")
        targets = resolver.resolve(event)

        assert set(targets) == {"creator1", "tech1"}

    def test_status_changed_excludes_actor(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        event = _make_event(EventType.REQUEST_STATUS_CHANGED, actor_id="tech1")
        targets = resolver.resolve(event)

        assert targets == ["creator1"]

    def test_assigned_targets_assigned_technician(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        event = _make_event(EventType.REQUEST_ASSIGNED, actor_id="actor1")
        targets = resolver.resolve(event)

        assert targets == ["tech1"]

    def test_assigned_excludes_actor_self_assign(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        event = _make_event(EventType.REQUEST_ASSIGNED, actor_id="tech1")
        targets = resolver.resolve(event)

        assert targets == []

    def test_priority_changed_targets_assigned(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        event = _make_event(EventType.REQUEST_PRIORITY_CHANGED, actor_id="actor1")
        targets = resolver.resolve(event)

        assert targets == ["tech1"]

    def test_priority_changed_no_assigned(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        event = _make_event(EventType.REQUEST_PRIORITY_CHANGED, actor_id="actor1", assigned_to=None)
        targets = resolver.resolve(event)

        assert targets == []

    def test_comment_added_targets_creator_and_assigned(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        event = _make_event(EventType.REQUEST_COMMENT_ADDED, actor_id="actor1")
        targets = resolver.resolve(event)

        assert set(targets) == {"creator1", "tech1"}

    def test_comment_added_excludes_author(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        event = _make_event(EventType.REQUEST_COMMENT_ADDED, actor_id="creator1")
        targets = resolver.resolve(event)

        assert targets == ["tech1"]

    def test_note_added_targets_assigned(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        event = _make_event(EventType.REQUEST_NOTE_ADDED, actor_id="actor1")
        targets = resolver.resolve(event)

        assert targets == ["tech1"]

    def test_note_added_excludes_author(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        event = _make_event(EventType.REQUEST_NOTE_ADDED, actor_id="tech1")
        targets = resolver.resolve(event)

        assert targets == []

    def test_no_duplicates(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        # created_by and assigned_to are the same person
        event = _make_event(
            EventType.REQUEST_STATUS_CHANGED,
            actor_id="actor1",
            created_by="tech1",
            assigned_to="tech1",
        )
        targets = resolver.resolve(event)

        assert targets == ["tech1"]

    def test_unknown_event_type_returns_empty(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        event = DomainEvent(
            event_type="unknown.event",
            company_id="comp1",
            actor_id="actor1",
            payload={},
            title="Test",
            body="Test",
        )
        targets = resolver.resolve(event)

        assert targets == []

    def test_report_ready_targets_requester(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        event = DomainEvent(
            event_type=EventType.REPORT_READY,
            company_id="comp1",
            actor_id="system",
            payload={"requested_by": "user1"},
            title="Report ready",
            body="Your report is ready",
        )
        targets = resolver.resolve(event)

        assert targets == ["user1"]

    def test_report_ready_no_requester_returns_empty(self):
        repo = MagicMock()
        resolver = TargetResolver(user_repo=repo)

        event = DomainEvent(
            event_type=EventType.REPORT_READY,
            company_id="comp1",
            actor_id="system",
            payload={},
            title="Report ready",
            body="Your report is ready",
        )
        targets = resolver.resolve(event)

        assert targets == []
