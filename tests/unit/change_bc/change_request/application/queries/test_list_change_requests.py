from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.change_bc.change_request.application.queries.list_change_requests import (
    ChangeRequestListDto,
    ListChangeRequestsQuery,
    ListChangeRequestsQueryHandler,
)
from src.change_bc.change_request.domain.entities import ChangeRequest
from src.change_bc.change_request.domain.enums import ChangeStatus, ChangeType


COMPANY_ID = "01COMPANY00000000000000001"
USER_ID = "01USER00000000000000000001"
ASSIGNEE_ID = "01ASSIGNEE0000000000000001"


def _make_change(**overrides) -> ChangeRequest:
    defaults = dict(
        id="01CHANGE000000000000000001",
        company_id=COMPANY_ID,
        requested_by=USER_ID,
        title="Install security patch",
    )
    defaults.update(overrides)
    return ChangeRequest.create(**defaults)


class TestListChangeRequestsQuery:
    def test_returns_dtos_with_correct_fields(self):
        change = _make_change()
        change.assigned_to = ASSIGNEE_ID
        change.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        change.updated_at = datetime(2026, 1, 2, tzinfo=timezone.utc)
        repo = MagicMock()
        repo.find_all.return_value = ([change], 1)
        handler = ListChangeRequestsQueryHandler(change_repo=repo)

        dtos, total = handler.handle(
            ListChangeRequestsQuery(company_id=COMPANY_ID)
        )

        assert total == 1
        assert len(dtos) == 1
        dto = dtos[0]
        assert dto.id == change.id
        assert dto.title == "Install security patch"
        assert dto.change_type == ChangeType.STANDARD.value
        assert dto.status == ChangeStatus.DRAFT.value
        assert dto.assigned_to == ASSIGNEE_ID
        assert dto.requested_by == USER_ID

    def test_passes_filters_to_repo(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)
        handler = ListChangeRequestsQueryHandler(change_repo=repo)

        handler.handle(
            ListChangeRequestsQuery(
                company_id=COMPANY_ID,
                page=2,
                page_size=10,
                status="scheduled",
                change_type="normal",
                assigned_to=ASSIGNEE_ID,
                search="patch",
            )
        )

        repo.find_all.assert_called_once()
        call_args = repo.find_all.call_args
        assert call_args[1]["company_id"] == COMPANY_ID
        filters = call_args[1]["filters"]
        assert filters.page == 2
        assert filters.page_size == 10
        assert filters.status == "scheduled"
        assert filters.change_type == "normal"
        assert filters.assigned_to == ASSIGNEE_ID
        assert filters.search == "patch"

    def test_user_name_resolver_called_with_user_ids(self):
        change1 = _make_change(id="01CHANGE000000000000000001")
        change1.assigned_to = ASSIGNEE_ID
        change2 = _make_change(
            id="01CHANGE000000000000000002",
            requested_by="01USER00000000000000000002",
        )
        repo = MagicMock()
        repo.find_all.return_value = ([change1, change2], 2)

        resolver = MagicMock(
            return_value={
                USER_ID: "John Doe",
                ASSIGNEE_ID: "Jane Admin",
                "01USER00000000000000000002": "Bob Smith",
            }
        )
        handler = ListChangeRequestsQueryHandler(
            change_repo=repo, user_name_resolver=resolver
        )

        dtos, total = handler.handle(
            ListChangeRequestsQuery(company_id=COMPANY_ID)
        )

        resolver.assert_called_once()
        called_ids = set(resolver.call_args[0][0])
        assert USER_ID in called_ids
        assert ASSIGNEE_ID in called_ids
        assert "01USER00000000000000000002" in called_ids

    def test_name_resolver_populates_dto_names(self):
        change = _make_change()
        change.assigned_to = ASSIGNEE_ID
        repo = MagicMock()
        repo.find_all.return_value = ([change], 1)

        resolver = MagicMock(
            return_value={
                USER_ID: "John Doe",
                ASSIGNEE_ID: "Jane Admin",
            }
        )
        handler = ListChangeRequestsQueryHandler(
            change_repo=repo, user_name_resolver=resolver
        )

        dtos, _ = handler.handle(
            ListChangeRequestsQuery(company_id=COMPANY_ID)
        )

        dto = dtos[0]
        assert dto.requested_by_name == "John Doe"
        assert dto.assigned_to_name == "Jane Admin"

    def test_no_resolver_names_are_none(self):
        change = _make_change()
        change.assigned_to = ASSIGNEE_ID
        repo = MagicMock()
        repo.find_all.return_value = ([change], 1)
        handler = ListChangeRequestsQueryHandler(change_repo=repo)

        dtos, _ = handler.handle(
            ListChangeRequestsQuery(company_id=COMPANY_ID)
        )

        dto = dtos[0]
        assert dto.requested_by_name is None
        assert dto.assigned_to_name is None

    def test_empty_results(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)
        handler = ListChangeRequestsQueryHandler(change_repo=repo)

        dtos, total = handler.handle(
            ListChangeRequestsQuery(company_id=COMPANY_ID)
        )

        assert dtos == []
        assert total == 0

    def test_assigned_to_none_name_is_none(self):
        change = _make_change()
        assert change.assigned_to is None
        repo = MagicMock()
        repo.find_all.return_value = ([change], 1)
        resolver = MagicMock(return_value={USER_ID: "John Doe"})
        handler = ListChangeRequestsQueryHandler(
            change_repo=repo, user_name_resolver=resolver
        )

        dtos, _ = handler.handle(
            ListChangeRequestsQuery(company_id=COMPANY_ID)
        )

        dto = dtos[0]
        assert dto.assigned_to is None
        assert dto.assigned_to_name is None
