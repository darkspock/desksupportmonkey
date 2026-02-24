from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.audit_bc.audit.application.queries.list_audit_entries import (
    ListAuditEntriesQuery,
    ListAuditEntriesQueryHandler,
)
from src.audit_bc.audit.domain.entities import AuditEntry


def _make_entry(entry_id="e1", actor_id="a1", actor_email="a@b.com"):
    return AuditEntry(
        id=entry_id, company_id="c1", actor_id=actor_id,
        actor_email=actor_email, action="test.created",
        resource_type="test", resource_id="r1",
        http_method="POST", http_path="/test",
        ip_address="1.2.3.4", user_agent=None,
        request_data=None, response_status=201,
        changes=None, hash="abc123",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


class TestListAuditEntriesQueryHandler:
    def _make_handler(self, entries=None, total=0):
        repo = MagicMock()
        repo.find_all.return_value = (entries or [], total)
        repo.find_tags_by_entry.return_value = []
        handler = ListAuditEntriesQueryHandler(repo=repo)
        return handler, repo

    def test_returns_paginated_results(self):
        entries = [_make_entry("e1"), _make_entry("e2")]
        handler, repo = self._make_handler(entries, 2)

        dtos, total = handler.handle(
            ListAuditEntriesQuery(company_id="c1", page=1, page_size=20)
        )

        assert total == 2
        assert len(dtos) == 2
        assert dtos[0].id == "e1"
        assert dtos[0].tag_count == 0

    def test_resolves_actor_names(self):
        entries = [_make_entry("e1", actor_id="a1")]
        handler, repo = self._make_handler(entries, 1)
        name_resolver = MagicMock(return_value={"a1": "Admin User"})
        handler.user_name_resolver = name_resolver

        dtos, _ = handler.handle(
            ListAuditEntriesQuery(company_id="c1")
        )

        assert dtos[0].actor_name == "Admin User"
        name_resolver.assert_called_once_with(["a1"])

    def test_empty_results(self):
        handler, repo = self._make_handler([], 0)

        dtos, total = handler.handle(
            ListAuditEntriesQuery(company_id="c1")
        )

        assert total == 0
        assert len(dtos) == 0
