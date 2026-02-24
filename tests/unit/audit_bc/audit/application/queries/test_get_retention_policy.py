from unittest.mock import MagicMock

from src.audit_bc.audit.application.queries.get_retention_policy import (
    GetRetentionPolicyQuery,
    GetRetentionPolicyQueryHandler,
)
from src.audit_bc.audit.domain.entities import RetentionPolicy


class TestGetRetentionPolicyQueryHandler:
    def _make_handler(self):
        repo = MagicMock()
        handler = GetRetentionPolicyQueryHandler(repo=repo)
        return handler, repo

    def test_returns_existing_policy(self):
        handler, repo = self._make_handler()
        policy = RetentionPolicy.create(
            company_id="c1",
            retention_months=60,
            updated_by="admin1",
        )
        repo.find_retention_policy.return_value = policy

        result = handler.handle(
            GetRetentionPolicyQuery(company_id="c1")
        )

        assert result.retention_months == 60
        assert result.updated_by == "admin1"
        assert result.updated_at is not None

    def test_returns_defaults_when_no_policy(self):
        handler, repo = self._make_handler()
        repo.find_retention_policy.return_value = None

        result = handler.handle(
            GetRetentionPolicyQuery(company_id="c1")
        )

        assert result.retention_months == 36
        assert result.updated_at is None
        assert result.updated_by is None
