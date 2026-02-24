from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.queries.get_gdpr_request import (
    GetGdprRequestQuery,
    GetGdprRequestQueryHandler,
)
from src.audit_bc.audit.domain.entities import GdprRequest
from src.audit_bc.audit.domain.enums import (
    GdprRequestStatus,
    GdprRequestType,
)
from src.audit_bc.audit.domain.exceptions import GdprRequestNotFoundError


class TestGetGdprRequestQueryHandler:
    def _make_handler(self):
        repo = MagicMock()
        handler = GetGdprRequestQueryHandler(repo=repo)
        return handler, repo

    def _make_request(self):
        return GdprRequest(
            id="req1",
            company_id="c1",
            target_user_id="u1",
            target_user_email="user@example.com",
            requested_by="admin1",
            request_type=GdprRequestType.EXPORT,
            status=GdprRequestStatus.COMPLETED,
            storage_key="gdpr-exports/c1/req1.zip",
        )

    def test_returns_request_detail(self):
        handler, repo = self._make_handler()
        repo.find_gdpr_request_by_id.return_value = self._make_request()

        dto = handler.handle(
            GetGdprRequestQuery(request_id="req1", company_id="c1")
        )

        assert dto.id == "req1"
        assert dto.target_user_email == "user@example.com"
        assert dto.request_type == "export"
        assert dto.status == "completed"
        assert dto.storage_key == "gdpr-exports/c1/req1.zip"

    def test_raises_when_not_found(self):
        handler, repo = self._make_handler()
        repo.find_gdpr_request_by_id.return_value = None

        with pytest.raises(GdprRequestNotFoundError):
            handler.handle(
                GetGdprRequestQuery(
                    request_id="nonexistent", company_id="c1"
                )
            )
