from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.queries.get_audit_entry import (
    GetAuditEntryQuery,
    GetAuditEntryQueryHandler,
)
from src.audit_bc.audit.domain.entities import (
    AuditEntry,
    AuditEntryTag,
    ComplianceControl,
)
from src.audit_bc.audit.domain.exceptions import AuditEntryNotFoundError


def _make_entry():
    return AuditEntry(
        id="e1", company_id="c1", actor_id="a1",
        actor_email="admin@example.com", action="asset.created",
        resource_type="asset", resource_id="r1",
        http_method="POST", http_path="/api/v1/assets",
        ip_address="1.2.3.4", user_agent="TestAgent",
        request_data={"name": "Laptop"}, response_status=201,
        changes=None, hash="abc123",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


class TestGetAuditEntryQueryHandler:
    def _make_handler(self):
        repo = MagicMock()
        handler = GetAuditEntryQueryHandler(repo=repo)
        return handler, repo

    def test_returns_detail_with_tags(self):
        handler, repo = self._make_handler()
        repo.find_by_id.return_value = _make_entry()
        repo.find_tags_by_entry.return_value = [
            AuditEntryTag(
                id="t1", audit_entry_id="e1", control_id="ctrl1",
                tagged_by="user1",
                tagged_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            )
        ]
        repo.find_control_by_id.return_value = ComplianceControl(
            id="ctrl1", company_id=None, code="NIS2-ART21-2A",
            name="Risk analysis", framework="NIS2", description=None,
            is_predefined=True, is_active=True,
        )

        detail = handler.handle(
            GetAuditEntryQuery(entry_id="e1", company_id="c1")
        )

        assert detail.id == "e1"
        assert detail.action == "asset.created"
        assert len(detail.tags) == 1
        assert detail.tags[0].control_code == "NIS2-ART21-2A"
        assert detail.tags[0].framework == "NIS2"

    def test_raises_not_found(self):
        handler, repo = self._make_handler()
        repo.find_by_id.return_value = None

        with pytest.raises(AuditEntryNotFoundError):
            handler.handle(
                GetAuditEntryQuery(entry_id="missing", company_id="c1")
            )

    def test_returns_detail_without_tags(self):
        handler, repo = self._make_handler()
        repo.find_by_id.return_value = _make_entry()
        repo.find_tags_by_entry.return_value = []

        detail = handler.handle(
            GetAuditEntryQuery(entry_id="e1", company_id="c1")
        )

        assert len(detail.tags) == 0
        assert detail.request_data == {"name": "Laptop"}
