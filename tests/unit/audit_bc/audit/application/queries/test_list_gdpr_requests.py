from unittest.mock import MagicMock

from src.audit_bc.audit.application.queries.list_gdpr_requests import (
    ListGdprRequestsQuery,
    ListGdprRequestsQueryHandler,
)
from src.audit_bc.audit.domain.entities import GdprRequest
from src.audit_bc.audit.domain.enums import (
    GdprRequestStatus,
    GdprRequestType,
)


class TestListGdprRequestsQueryHandler:
    def _make_handler(self):
        repo = MagicMock()
        handler = ListGdprRequestsQueryHandler(repo=repo)
        return handler, repo

    def _make_request(self):
        return GdprRequest(
            id="req1",
            company_id="c1",
            target_user_id="u1",
            target_user_email="user@example.com",
            requested_by="admin1",
            request_type=GdprRequestType.EXPORT,
            status=GdprRequestStatus.PENDING,
        )

    def test_returns_paginated_results(self):
        handler, repo = self._make_handler()
        repo.find_gdpr_requests.return_value = (
            [self._make_request()], 1
        )

        dtos, total = handler.handle(
            ListGdprRequestsQuery(company_id="c1", page=1, page_size=20)
        )

        assert total == 1
        assert len(dtos) == 1
        assert dtos[0].id == "req1"
        assert dtos[0].request_type == "export"
        assert dtos[0].status == "pending"

    def test_returns_empty_when_no_requests(self):
        handler, repo = self._make_handler()
        repo.find_gdpr_requests.return_value = ([], 0)

        dtos, total = handler.handle(
            ListGdprRequestsQuery(company_id="c1")
        )

        assert total == 0
        assert len(dtos) == 0

    def test_passes_filters_to_repo(self):
        handler, repo = self._make_handler()
        repo.find_gdpr_requests.return_value = ([], 0)

        handler.handle(
            ListGdprRequestsQuery(
                company_id="c1",
                page=2,
                page_size=10,
                status="completed",
                request_type="export",
                search="user@",
            )
        )

        call_args = repo.find_gdpr_requests.call_args
        assert call_args[0][0] == "c1"
        filters = call_args[0][1]
        assert filters["page"] == 2
        assert filters["page_size"] == 10
        assert filters["status"] == "completed"
        assert filters["request_type"] == "export"
        assert filters["search"] == "user@"
