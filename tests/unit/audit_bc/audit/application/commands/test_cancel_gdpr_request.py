from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.commands.cancel_gdpr_request import (
    CancelGdprRequestCommand,
    CancelGdprRequestHandler,
)
from src.audit_bc.audit.domain.entities import GdprRequest
from src.audit_bc.audit.domain.enums import (
    GdprRequestStatus,
    GdprRequestType,
)
from src.audit_bc.audit.domain.exceptions import (
    GdprRequestNotFoundError,
    InvalidGdprStatusTransitionError,
)


class TestCancelGdprRequestHandler:
    def _make_handler(self):
        repo = MagicMock()
        handler = CancelGdprRequestHandler(repo=repo)
        return handler, repo

    def _make_request(self, status=GdprRequestStatus.PENDING):
        return GdprRequest(
            id="req1",
            company_id="c1",
            target_user_id="u1",
            target_user_email="user@example.com",
            requested_by="admin1",
            request_type=GdprRequestType.EXPORT,
            status=status,
        )

    def test_cancels_pending_request(self):
        handler, repo = self._make_handler()
        repo.find_gdpr_request_by_id.return_value = self._make_request()

        handler.handle(
            CancelGdprRequestCommand(
                request_id="req1", company_id="c1"
            )
        )

        repo.save_gdpr_request.assert_called_once()
        saved = repo.save_gdpr_request.call_args[0][0]
        assert saved.status == GdprRequestStatus.CANCELLED

    def test_raises_when_not_found(self):
        handler, repo = self._make_handler()
        repo.find_gdpr_request_by_id.return_value = None

        with pytest.raises(GdprRequestNotFoundError):
            handler.handle(
                CancelGdprRequestCommand(
                    request_id="req1", company_id="c1"
                )
            )

    def test_raises_when_not_pending(self):
        handler, repo = self._make_handler()
        repo.find_gdpr_request_by_id.return_value = self._make_request(
            status=GdprRequestStatus.PROCESSING
        )

        with pytest.raises(InvalidGdprStatusTransitionError):
            handler.handle(
                CancelGdprRequestCommand(
                    request_id="req1", company_id="c1"
                )
            )
