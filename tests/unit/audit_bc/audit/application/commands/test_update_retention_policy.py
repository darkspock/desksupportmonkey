from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.commands.update_retention_policy import (
    UpdateRetentionPolicyCommand,
    UpdateRetentionPolicyHandler,
)
from src.audit_bc.audit.domain.entities import RetentionPolicy
from src.audit_bc.audit.domain.exceptions import (
    InvalidRetentionPeriodError,
)


class TestUpdateRetentionPolicyHandler:
    def _make_handler(self):
        repo = MagicMock()
        handler = UpdateRetentionPolicyHandler(repo=repo)
        return handler, repo

    def test_creates_new_policy(self):
        handler, repo = self._make_handler()
        repo.find_retention_policy.return_value = None

        handler.handle(
            UpdateRetentionPolicyCommand(
                company_id="c1",
                retention_months=60,
                updated_by="admin1",
            )
        )

        repo.save_retention_policy.assert_called_once()
        saved = repo.save_retention_policy.call_args[0][0]
        assert isinstance(saved, RetentionPolicy)
        assert saved.retention_months == 60
        assert saved.company_id == "c1"
        assert saved.updated_by == "admin1"

    def test_updates_existing_policy(self):
        handler, repo = self._make_handler()
        existing = RetentionPolicy.create(
            company_id="c1",
            retention_months=36,
            updated_by="admin1",
        )
        repo.find_retention_policy.return_value = existing

        handler.handle(
            UpdateRetentionPolicyCommand(
                company_id="c1",
                retention_months=84,
                updated_by="admin2",
            )
        )

        repo.save_retention_policy.assert_called_once()
        saved = repo.save_retention_policy.call_args[0][0]
        assert saved.retention_months == 84
        assert saved.updated_by == "admin2"

    def test_rejects_invalid_period(self):
        handler, repo = self._make_handler()

        with pytest.raises(InvalidRetentionPeriodError):
            handler.handle(
                UpdateRetentionPolicyCommand(
                    company_id="c1",
                    retention_months=15,
                    updated_by="admin1",
                )
            )

        repo.save_retention_policy.assert_not_called()

    def test_accepts_indefinite(self):
        handler, repo = self._make_handler()
        repo.find_retention_policy.return_value = None

        handler.handle(
            UpdateRetentionPolicyCommand(
                company_id="c1",
                retention_months=0,
                updated_by="admin1",
            )
        )

        saved = repo.save_retention_policy.call_args[0][0]
        assert saved.retention_months == 0
