from unittest.mock import MagicMock, call

import pytest

from src.request_bc.request.application.commands.approve_request import (
    ApproveRequestCommand,
    ApproveRequestCommandHandler,
    NotPendingApprovalError,
    RequestNotFoundError as ApproveNotFoundError,
    UnauthorizedApprovalError,
)
from src.request_bc.request.application.commands.reject_request import (
    NotPendingApprovalError as RejectNotPendingError,
    RejectRequestCommand,
    RejectRequestCommandHandler,
    RequestNotFoundError as RejectNotFoundError,
    UnauthorizedRejectionError,
)
from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.domain.enums import RequestPriority, RequestStatus, RequestType


def _make_pending_request(**overrides):
    r = ServiceRequest(
        id="req1",
        company_id="comp1",
        created_by="user1",
        type=RequestType.NEW_EQUIPMENT,
        title="New laptop",
        description="I need a laptop",
        status=RequestStatus.PENDING_APPROVAL,
        priority=RequestPriority.LOW,
    )
    for k, v in overrides.items():
        setattr(r, k, v)
    return r


def _make_repo(request=None):
    repo = MagicMock()
    repo.find_by_id.return_value = request
    repo.save.side_effect = lambda r: r
    return repo


# ---------------------------------------------------------------------------
# ApproveRequestCommandHandler
# ---------------------------------------------------------------------------


class TestApproveRequestCommand:
    def test_admin_can_approve(self):
        request = _make_pending_request()
        repo = _make_repo(request)
        handler = ApproveRequestCommandHandler(request_repo=repo)

        handler.handle(
            ApproveRequestCommand(
                request_id="req1",
                company_id="comp1",
                performed_by="admin1",
                performed_by_role="admin",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.status == RequestStatus.SUBMITTED

    def test_super_admin_can_approve(self):
        request = _make_pending_request()
        repo = _make_repo(request)
        handler = ApproveRequestCommandHandler(request_repo=repo)

        handler.handle(
            ApproveRequestCommand(
                request_id="req1",
                company_id="comp1",
                performed_by="superadmin1",
                performed_by_role="super_admin",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.status == RequestStatus.SUBMITTED

    def test_department_manager_can_approve(self):
        request = _make_pending_request()
        repo = _make_repo(request)
        handler = ApproveRequestCommandHandler(request_repo=repo)

        handler.handle(
            ApproveRequestCommand(
                request_id="req1",
                company_id="comp1",
                performed_by="manager1",
                performed_by_role="technician",
                department_manager_id="manager1",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.status == RequestStatus.SUBMITTED

    def test_non_manager_non_admin_cannot_approve(self):
        request = _make_pending_request()
        repo = _make_repo(request)
        handler = ApproveRequestCommandHandler(request_repo=repo)

        with pytest.raises(UnauthorizedApprovalError):
            handler.handle(
                ApproveRequestCommand(
                    request_id="req1",
                    company_id="comp1",
                    performed_by="tech1",
                    performed_by_role="technician",
                    department_manager_id="manager1",  # different manager
                )
            )

    def test_wrong_manager_cannot_approve(self):
        request = _make_pending_request()
        repo = _make_repo(request)
        handler = ApproveRequestCommandHandler(request_repo=repo)

        with pytest.raises(UnauthorizedApprovalError):
            handler.handle(
                ApproveRequestCommand(
                    request_id="req1",
                    company_id="comp1",
                    performed_by="other_manager",
                    performed_by_role="technician",
                    department_manager_id="manager1",  # not the same as performed_by
                )
            )

    def test_request_not_found_raises(self):
        repo = _make_repo(None)
        handler = ApproveRequestCommandHandler(request_repo=repo)

        with pytest.raises(ApproveNotFoundError):
            handler.handle(
                ApproveRequestCommand(
                    request_id="missing",
                    company_id="comp1",
                    performed_by="admin1",
                    performed_by_role="admin",
                )
            )

    def test_not_pending_approval_raises(self):
        request = _make_pending_request(status=RequestStatus.SUBMITTED)
        repo = _make_repo(request)
        handler = ApproveRequestCommandHandler(request_repo=repo)

        with pytest.raises(NotPendingApprovalError):
            handler.handle(
                ApproveRequestCommand(
                    request_id="req1",
                    company_id="comp1",
                    performed_by="admin1",
                    performed_by_role="admin",
                )
            )

    def test_event_saved_with_approved_by(self):
        request = _make_pending_request()
        repo = _make_repo(request)
        handler = ApproveRequestCommandHandler(request_repo=repo)

        handler.handle(
            ApproveRequestCommand(
                request_id="req1",
                company_id="comp1",
                performed_by="admin1",
                performed_by_role="admin",
            )
        )

        repo.save_event.assert_called_once()
        saved_event = repo.save_event.call_args[0][0]
        assert saved_event.event_type == "approved"
        assert saved_event.data["approved_by"] == "admin1"

    def test_repo_queried_with_correct_company(self):
        repo = _make_repo(None)
        handler = ApproveRequestCommandHandler(request_repo=repo)

        with pytest.raises(ApproveNotFoundError):
            handler.handle(
                ApproveRequestCommand(
                    request_id="req1",
                    company_id="comp1",
                    performed_by="admin1",
                    performed_by_role="admin",
                )
            )

        repo.find_by_id.assert_called_once_with("req1", "comp1")


# ---------------------------------------------------------------------------
# RejectRequestCommandHandler
# ---------------------------------------------------------------------------


class TestRejectRequestCommand:
    def test_admin_can_reject(self):
        request = _make_pending_request()
        repo = _make_repo(request)
        handler = RejectRequestCommandHandler(request_repo=repo)

        handler.handle(
            RejectRequestCommand(
                request_id="req1",
                company_id="comp1",
                performed_by="admin1",
                performed_by_role="admin",
                reason="Not in budget",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.status == RequestStatus.REJECTED
        assert saved.resolved_at is not None

    def test_department_manager_can_reject(self):
        request = _make_pending_request()
        repo = _make_repo(request)
        handler = RejectRequestCommandHandler(request_repo=repo)

        handler.handle(
            RejectRequestCommand(
                request_id="req1",
                company_id="comp1",
                performed_by="manager1",
                performed_by_role="technician",
                reason="Not justified",
                department_manager_id="manager1",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.status == RequestStatus.REJECTED

    def test_empty_reason_raises(self):
        request = _make_pending_request()
        repo = _make_repo(request)
        handler = RejectRequestCommandHandler(request_repo=repo)

        with pytest.raises(ValueError, match="reason"):
            handler.handle(
                RejectRequestCommand(
                    request_id="req1",
                    company_id="comp1",
                    performed_by="admin1",
                    performed_by_role="admin",
                    reason="",
                )
            )

    def test_whitespace_only_reason_raises(self):
        request = _make_pending_request()
        repo = _make_repo(request)
        handler = RejectRequestCommandHandler(request_repo=repo)

        with pytest.raises(ValueError, match="reason"):
            handler.handle(
                RejectRequestCommand(
                    request_id="req1",
                    company_id="comp1",
                    performed_by="admin1",
                    performed_by_role="admin",
                    reason="   ",
                )
            )

    def test_unauthorized_user_cannot_reject(self):
        request = _make_pending_request()
        repo = _make_repo(request)
        handler = RejectRequestCommandHandler(request_repo=repo)

        with pytest.raises(UnauthorizedRejectionError):
            handler.handle(
                RejectRequestCommand(
                    request_id="req1",
                    company_id="comp1",
                    performed_by="employee1",
                    performed_by_role="employee",
                    reason="Nope",
                )
            )

    def test_request_not_found_raises(self):
        repo = _make_repo(None)
        handler = RejectRequestCommandHandler(request_repo=repo)

        with pytest.raises(RejectNotFoundError):
            handler.handle(
                RejectRequestCommand(
                    request_id="missing",
                    company_id="comp1",
                    performed_by="admin1",
                    performed_by_role="admin",
                    reason="Budget",
                )
            )

    def test_not_pending_approval_raises(self):
        request = _make_pending_request(status=RequestStatus.IN_REVIEW)
        repo = _make_repo(request)
        handler = RejectRequestCommandHandler(request_repo=repo)

        with pytest.raises(RejectNotPendingError):
            handler.handle(
                RejectRequestCommand(
                    request_id="req1",
                    company_id="comp1",
                    performed_by="admin1",
                    performed_by_role="admin",
                    reason="Budget",
                )
            )

    def test_event_saved_with_reason_and_rejected_by(self):
        request = _make_pending_request()
        repo = _make_repo(request)
        handler = RejectRequestCommandHandler(request_repo=repo)

        handler.handle(
            RejectRequestCommand(
                request_id="req1",
                company_id="comp1",
                performed_by="admin1",
                performed_by_role="admin",
                reason="  Not in budget  ",
            )
        )

        repo.save_event.assert_called_once()
        saved_event = repo.save_event.call_args[0][0]
        assert saved_event.event_type == "rejected"
        assert saved_event.data["rejected_by"] == "admin1"
        assert saved_event.data["reason"] == "Not in budget"  # stripped
