from unittest.mock import MagicMock

import pytest

from src.request_bc.request.application.commands.create_request import (
    CreateRequestCommand,
    CreateRequestCommandHandler,
)
from src.request_bc.request.application.commands.change_request_status import (
    ChangeRequestStatusCommand,
    ChangeRequestStatusCommandHandler,
    RequestNotFoundError as StatusNotFoundError,
)
from src.request_bc.request.application.commands.change_request_priority import (
    ChangeRequestPriorityCommand,
    ChangeRequestPriorityCommandHandler,
    RequestNotFoundError as PriorityNotFoundError,
)
from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.domain.enums import (
    InvalidStatusTransitionError,
    RequestPriority,
    RequestStatus,
    RequestType,
)


def _make_request(**overrides):
    defaults = dict(
        company_id="comp1",
        created_by="user1",
        type=RequestType.INCIDENT,
        title="Test request",
        description="Test description",
    )
    defaults.update(overrides)
    return ServiceRequest.create(**defaults)


def _make_repo(request=None):
    repo = MagicMock()
    repo.save.side_effect = lambda r: r
    repo.find_by_id.return_value = request
    return repo


class TestCreateRequestCommand:
    def test_success_incident_auto_priority(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        result = handler.handle(
            CreateRequestCommand(
                company_id="comp1",
                created_by="user1",
                type="incident",
                title="Laptop broken",
                description="Screen cracked",
            )
        )

        assert result.type == RequestType.INCIDENT
        assert result.priority == RequestPriority.HIGH
        assert result.status == RequestStatus.SUBMITTED
        assert repo.save.call_count == 1
        assert repo.save_event.call_count == 1
        event = repo.save_event.call_args[0][0]
        assert event.event_type == "created"

    def test_success_new_equipment_auto_priority(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        result = handler.handle(
            CreateRequestCommand(
                company_id="comp1",
                created_by="user1",
                type="new_equipment",
                title="Need monitor",
                description="Second monitor",
            )
        )

        assert result.priority == RequestPriority.LOW

    def test_success_with_data(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        result = handler.handle(
            CreateRequestCommand(
                company_id="comp1",
                created_by="user1",
                type="incident",
                title="Laptop broken",
                description="Screen cracked",
                data={"asset_id": "asset123"},
            )
        )

        assert result.data == {"asset_id": "asset123"}

    def test_invalid_type_raises(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        with pytest.raises(ValueError):
            handler.handle(
                CreateRequestCommand(
                    company_id="comp1",
                    created_by="user1",
                    type="invalid_type",
                    title="Test",
                    description="Test",
                )
            )


class TestChangeRequestStatusCommand:
    def test_success(self):
        request = _make_request()
        repo = _make_repo(request)
        handler = ChangeRequestStatusCommandHandler(request_repo=repo)

        result = handler.handle(
            ChangeRequestStatusCommand(
                request_id=request.id,
                company_id="comp1",
                new_status="in_review",
                performed_by="tech1",
            )
        )

        assert result.status == RequestStatus.IN_REVIEW
        assert repo.save_event.call_count >= 1

    def test_not_found_raises(self):
        repo = _make_repo(None)
        handler = ChangeRequestStatusCommandHandler(request_repo=repo)

        with pytest.raises(StatusNotFoundError):
            handler.handle(
                ChangeRequestStatusCommand(
                    request_id="bad",
                    company_id="comp1",
                    new_status="in_review",
                    performed_by="tech1",
                )
            )

    def test_invalid_transition_raises(self):
        request = _make_request()
        repo = _make_repo(request)
        handler = ChangeRequestStatusCommandHandler(request_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                ChangeRequestStatusCommand(
                    request_id=request.id,
                    company_id="comp1",
                    new_status="resolved",
                    performed_by="tech1",
                )
            )

    def test_auto_assign_on_in_review(self):
        request = _make_request()
        assert request.assigned_to is None
        repo = _make_repo(request)
        handler = ChangeRequestStatusCommandHandler(request_repo=repo)

        result = handler.handle(
            ChangeRequestStatusCommand(
                request_id=request.id,
                company_id="comp1",
                new_status="in_review",
                performed_by="tech1",
            )
        )

        assert result.assigned_to == "tech1"
        # Two events: status_changed + assigned
        assert repo.save_event.call_count == 2
        events = [call[0][0] for call in repo.save_event.call_args_list]
        assert events[0].event_type == "status_changed"
        assert events[1].event_type == "assigned"
        assert events[1].data["reason"] == "auto_assign_on_review"

    def test_no_auto_assign_if_already_assigned(self):
        request = _make_request()
        request.assign("other_tech")
        repo = _make_repo(request)
        handler = ChangeRequestStatusCommandHandler(request_repo=repo)

        result = handler.handle(
            ChangeRequestStatusCommand(
                request_id=request.id,
                company_id="comp1",
                new_status="in_review",
                performed_by="tech1",
            )
        )

        assert result.assigned_to == "other_tech"
        # Only one event: status_changed (no auto-assign)
        assert repo.save_event.call_count == 1


class TestChangeRequestPriorityCommand:
    def test_success(self):
        request = _make_request()
        repo = _make_repo(request)
        handler = ChangeRequestPriorityCommandHandler(request_repo=repo)

        result = handler.handle(
            ChangeRequestPriorityCommand(
                request_id=request.id,
                company_id="comp1",
                new_priority="urgent",
                performed_by="tech1",
            )
        )

        assert result.priority == RequestPriority.URGENT
        event = repo.save_event.call_args[0][0]
        assert event.event_type == "priority_changed"
        assert event.data["old_priority"] == "high"  # incident default
        assert event.data["new_priority"] == "urgent"

    def test_not_found_raises(self):
        repo = _make_repo(None)
        handler = ChangeRequestPriorityCommandHandler(request_repo=repo)

        with pytest.raises(PriorityNotFoundError):
            handler.handle(
                ChangeRequestPriorityCommand(
                    request_id="bad",
                    company_id="comp1",
                    new_priority="urgent",
                    performed_by="tech1",
                )
            )

    def test_invalid_priority_raises(self):
        request = _make_request()
        repo = _make_repo(request)
        handler = ChangeRequestPriorityCommandHandler(request_repo=repo)

        with pytest.raises(ValueError):
            handler.handle(
                ChangeRequestPriorityCommand(
                    request_id=request.id,
                    company_id="comp1",
                    new_priority="invalid",
                    performed_by="tech1",
                )
            )
