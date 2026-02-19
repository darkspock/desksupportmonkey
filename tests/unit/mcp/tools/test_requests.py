"""Unit tests for MCP request tools."""
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip(
    "mcp", reason="mcp package required for MCP tool tests"
)

from adapters.mcp.tools.requests import (  # noqa: E402
    handle_add_comment,
    handle_add_note,
    handle_assign_request,
    handle_change_request_priority,
    handle_change_request_status,
    handle_create_request,
    handle_get_request,
    handle_list_comments,
    handle_list_notes,
    handle_list_requests,
)
from core.tenant import TenantContext  # noqa: E402
from src.request_bc.request.application import (  # noqa: E402
    commands as _cmds,
    queries as _qrs,
)
from src.request_bc.request.domain.entities import (  # noqa: E402
    RequestComment,
    RequestNote,
    ServiceRequest,
)
from src.request_bc.request.domain.enums import (  # noqa: E402
    InvalidStatusTransitionError,
    RequestPriority,
    RequestStatus,
    RequestType,
)

CommentRequestNotFoundError = (
    _cmds.add_comment.RequestNotFoundError
)
NoteRequestNotFoundError = (
    _cmds.add_note.RequestNotFoundError
)
UserInactiveError = _cmds.assign_request.UserInactiveError
PriorityRequestNotFoundError = (
    _cmds.change_request_priority.RequestNotFoundError
)
RequestDetail = _qrs.get_request.RequestDetail
RequestNotFoundError = (
    _qrs.get_request.RequestNotFoundError
)
NotesListRequestNotFoundError = (
    _qrs.list_notes.RequestNotFoundError
)


def _make_request(**overrides) -> ServiceRequest:
    defaults = {
        "id": "req-1",
        "company_id": "company-1",
        "created_by": "user-1",
        "type": RequestType.INCIDENT,
        "title": "Laptop broken",
        "description": "Screen flickering",
        "status": RequestStatus.SUBMITTED,
        "priority": RequestPriority.HIGH,
        "assigned_to": None,
        "data": None,
        "resolved_at": None,
        "created_at": datetime(2024, 1, 15, 10, 0, 0),
        "updated_at": datetime(2024, 1, 15, 10, 0, 0),
    }
    defaults.update(overrides)
    return ServiceRequest(**defaults)


def _make_tenant(**overrides) -> TenantContext:
    defaults = {
        "company_id": "company-1",
        "user_id": "user-1",
        "role": "technician",
    }
    defaults.update(overrides)
    return TenantContext(**defaults)


def _parse_result(result):
    assert len(result) == 1
    return json.loads(result[0].text)


@pytest.fixture
def mock_db():
    with patch(
        "adapters.mcp.tools.requests.SessionLocal"
    ) as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


@pytest.fixture
def mock_tenant():
    tenant = _make_tenant()
    with patch(
        "adapters.mcp.tools.requests.get_tenant",
        return_value=tenant,
    ):
        yield tenant


_P = "adapters.mcp.tools.requests"


class TestCreateRequest:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        req = _make_request()

        with patch(
            f"{_P}.CreateRequestCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ) as MockRepo:
            MockHandler.return_value.handle.return_value = (
                None
            )
            MockRepo.return_value.find_all.return_value = (
                [req], 1,
            )

            result = await handle_create_request({
                "type": "incident",
                "title": "Laptop broken",
                "description": "Screen flickering",
            })

        data = _parse_result(result)
        assert data["title"] == "Laptop broken"
        assert data["type"] == "incident"

    @pytest.mark.asyncio
    async def test_invalid_type(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.CreateRequestCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                ValueError(
                    "'invalid' is not a valid "
                    "RequestType"
                )
            )

            result = await handle_create_request({
                "type": "invalid",
                "title": "Test",
                "description": "Test",
            })

        data = _parse_result(result)
        assert "error" in data


class TestListRequests:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        requests = [
            _make_request(),
            _make_request(
                id="req-2", title="Printer jam",
            ),
        ]

        with patch(
            f"{_P}.ListRequestsQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                requests, 2,
            )

            result = await handle_list_requests({})

        data = _parse_result(result)
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_with_filters(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.ListRequestsQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                [], 0,
            )

            result = await handle_list_requests({
                "status": "submitted",
                "priority": "high",
            })

        data = _parse_result(result)
        assert data["total"] == 0


class TestGetRequest:
    @pytest.mark.asyncio
    async def test_success_technician(
        self, mock_db, mock_tenant,
    ):
        req = _make_request()
        detail = RequestDetail(
            request=req, comment_count=3,
        )

        with patch(
            f"{_P}.GetRequestQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                detail
            )

            result = await handle_get_request({
                "request_id": "req-1",
            })

        data = _parse_result(result)
        assert data["id"] == "req-1"
        assert data["comment_count"] == 3

    @pytest.mark.asyncio
    async def test_employee_own_request(self, mock_db):
        tenant = _make_tenant(
            role="employee", user_id="user-1",
        )
        with patch(
            f"{_P}.get_tenant",
            return_value=tenant,
        ):
            req = _make_request(created_by="user-1")
            detail = RequestDetail(
                request=req, comment_count=0,
            )

            with patch(
                f"{_P}.GetRequestQueryHandler"
            ) as MockHandler, patch(
                f"{_P}.RequestRepository"
            ):
                MockHandler.return_value.handle \
                    .return_value = detail

                result = await handle_get_request({
                    "request_id": "req-1",
                })

            data = _parse_result(result)
            assert data["id"] == "req-1"

    @pytest.mark.asyncio
    async def test_employee_other_request_denied(
        self, mock_db,
    ):
        tenant = _make_tenant(
            role="employee", user_id="user-1",
        )
        with patch(
            f"{_P}.get_tenant",
            return_value=tenant,
        ):
            req = _make_request(
                created_by="user-other",
            )
            detail = RequestDetail(
                request=req, comment_count=0,
            )

            with patch(
                f"{_P}.GetRequestQueryHandler"
            ) as MockHandler, patch(
                f"{_P}.RequestRepository"
            ):
                MockHandler.return_value.handle \
                    .return_value = detail

                result = await handle_get_request({
                    "request_id": "req-1",
                })

            data = _parse_result(result)
            assert "error" in data
            assert "not found" in data["error"]

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.GetRequestQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                RequestNotFoundError(
                    "Request 'xyz' not found"
                )
            )

            result = await handle_get_request({
                "request_id": "xyz",
            })

        data = _parse_result(result)
        assert "error" in data


class TestChangeRequestStatus:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        req = _make_request(
            status=RequestStatus.IN_REVIEW,
        )
        detail = RequestDetail(
            request=req, comment_count=0,
        )

        with patch(
            f"{_P}.ChangeRequestStatusCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetRequestQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.RequestRepository"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                detail
            )

            result = await handle_change_request_status({
                "request_id": "req-1",
                "new_status": "in_review",
            })

        data = _parse_result(result)
        assert data["status"] == "in_review"

    @pytest.mark.asyncio
    async def test_invalid_transition(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.ChangeRequestStatusCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.RequestRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                InvalidStatusTransitionError(
                    RequestStatus.RESOLVED,
                    RequestStatus.SUBMITTED,
                )
            )

            result = await handle_change_request_status({
                "request_id": "req-1",
                "new_status": "submitted",
            })

        data = _parse_result(result)
        assert "error" in data


class TestChangeRequestPriority:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        req = _make_request(
            priority=RequestPriority.URGENT,
        )
        detail = RequestDetail(
            request=req, comment_count=0,
        )

        with patch(
            f"{_P}.ChangeRequestPriorityCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetRequestQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.RequestRepository"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                detail
            )

            result = await handle_change_request_priority({
                "request_id": "req-1",
                "new_priority": "urgent",
            })

        data = _parse_result(result)
        assert data["priority"] == "urgent"

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.ChangeRequestPriorityCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.RequestRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                PriorityRequestNotFoundError(
                    "Request 'xyz' not found"
                )
            )

            result = await handle_change_request_priority({
                "request_id": "xyz",
                "new_priority": "urgent",
            })

        data = _parse_result(result)
        assert "error" in data


class TestAssignRequest:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        req = _make_request(assigned_to="user-2")
        detail = RequestDetail(
            request=req, comment_count=0,
        )

        with patch(
            f"{_P}.AssignRequestCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetRequestQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.RequestRepository"
        ), patch(
            f"{_P}.UserRepository"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                detail
            )

            result = await handle_assign_request({
                "request_id": "req-1",
                "user_id": "user-2",
            })

        data = _parse_result(result)
        assert data["assigned_to"] == "user-2"

    @pytest.mark.asyncio
    async def test_user_inactive(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.AssignRequestCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.RequestRepository"
        ), patch(
            f"{_P}.UserRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                UserInactiveError(
                    "User 'user-2' is inactive"
                )
            )

            result = await handle_assign_request({
                "request_id": "req-1",
                "user_id": "user-2",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "inactive" in data["error"]


class TestAddComment:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.AddCommentCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                None
            )

            result = await handle_add_comment({
                "request_id": "req-1",
                "body": "Looking into this",
            })

        data = _parse_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_request_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.AddCommentCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                CommentRequestNotFoundError(
                    "Request 'xyz' not found"
                )
            )

            result = await handle_add_comment({
                "request_id": "xyz",
                "body": "Hello",
            })

        data = _parse_result(result)
        assert "error" in data


class TestListComments:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        comments = [
            RequestComment(
                id="c-1",
                request_id="req-1",
                author_id="user-1",
                body="Test comment",
                created_at=datetime(
                    2024, 1, 15, 10, 0, 0,
                ),
            ),
        ]

        with patch(
            f"{_P}.ListCommentsQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                comments
            )

            result = await handle_list_comments({
                "request_id": "req-1",
            })

        data = _parse_result(result)
        assert len(data) == 1
        assert data[0]["body"] == "Test comment"
        assert data[0]["author_id"] == "user-1"


class TestAddNote:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.AddNoteCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                None
            )

            result = await handle_add_note({
                "request_id": "req-1",
                "body": "Internal note",
            })

        data = _parse_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_request_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.AddNoteCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                NoteRequestNotFoundError(
                    "Request 'xyz' not found"
                )
            )

            result = await handle_add_note({
                "request_id": "xyz",
                "body": "Internal note",
            })

        data = _parse_result(result)
        assert "error" in data


class TestListNotes:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        notes = [
            RequestNote(
                id="n-1",
                request_id="req-1",
                author_id="user-1",
                body="Internal note content",
                created_at=datetime(
                    2024, 1, 15, 10, 0, 0,
                ),
            ),
        ]

        with patch(
            f"{_P}.ListNotesQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                notes
            )

            result = await handle_list_notes({
                "request_id": "req-1",
            })

        data = _parse_result(result)
        assert len(data) == 1
        assert data[0]["body"] == "Internal note content"
        assert data[0]["author_id"] == "user-1"

    @pytest.mark.asyncio
    async def test_request_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.ListNotesQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                NotesListRequestNotFoundError(
                    "Request 'xyz' not found"
                )
            )

            result = await handle_list_notes({
                "request_id": "xyz",
            })

        data = _parse_result(result)
        assert "error" in data
