from unittest.mock import MagicMock

import pytest

from src.request_bc.request.application.commands.assign_request import (
    AssignRequestCommand,
    AssignRequestCommandHandler,
    RequestNotFoundError,
    UserNotFoundError,
    UserInactiveError,
)
from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.domain.enums import RequestType


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


def _make_user(user_id="tech1", is_active=True):
    user = MagicMock()
    user.id = user_id
    user.is_active = is_active
    user.department_id = "dept1"
    return user


def _make_handler(request=None, user=None):
    request_repo = MagicMock()
    request_repo.save.side_effect = lambda r: r
    request_repo.find_by_id.return_value = request

    user_repo = MagicMock()
    user_repo.find_by_id_and_company.return_value = user

    handler = AssignRequestCommandHandler(
        request_repo=request_repo,
        user_repo=user_repo,
    )
    return handler, request_repo, user_repo


class TestAssignRequestCommand:
    def test_success(self):
        request = _make_request()
        user = _make_user()
        handler, request_repo, user_repo = _make_handler(request, user)

        result = handler.handle(
            AssignRequestCommand(
                request_id=request.id,
                company_id="comp1",
                user_id="tech1",
                performed_by="admin1",
            )
        )

        assert result.assigned_to == "tech1"
        assert request_repo.save.call_count == 1
        assert request_repo.save_event.call_count == 1
        event = request_repo.save_event.call_args[0][0]
        assert event.event_type == "assigned"
        assert event.data["assigned_to"] == "tech1"
        assert event.data["assigned_by"] == "admin1"

    def test_request_not_found(self):
        handler, _, _ = _make_handler(None, None)

        with pytest.raises(RequestNotFoundError):
            handler.handle(
                AssignRequestCommand(
                    request_id="bad",
                    company_id="comp1",
                    user_id="tech1",
                    performed_by="admin1",
                )
            )

    def test_user_not_found(self):
        request = _make_request()
        handler, _, _ = _make_handler(request, None)

        with pytest.raises(UserNotFoundError):
            handler.handle(
                AssignRequestCommand(
                    request_id=request.id,
                    company_id="comp1",
                    user_id="bad_user",
                    performed_by="admin1",
                )
            )

    def test_user_inactive(self):
        request = _make_request()
        user = _make_user(is_active=False)
        handler, _, _ = _make_handler(request, user)

        with pytest.raises(UserInactiveError):
            handler.handle(
                AssignRequestCommand(
                    request_id=request.id,
                    company_id="comp1",
                    user_id="tech1",
                    performed_by="admin1",
                )
            )

    def test_reassign(self):
        request = _make_request()
        request.assign("old_tech")
        assert request.assigned_to == "old_tech"

        user = _make_user(user_id="new_tech")
        handler, request_repo, _ = _make_handler(request, user)

        result = handler.handle(
            AssignRequestCommand(
                request_id=request.id,
                company_id="comp1",
                user_id="new_tech",
                performed_by="admin1",
            )
        )

        assert result.assigned_to == "new_tech"
