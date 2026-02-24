from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.commands.remove_audit_tag import (
    RemoveAuditTagCommand,
    RemoveAuditTagHandler,
)
from src.audit_bc.audit.domain.entities import AuditEntry
from src.audit_bc.audit.domain.exceptions import AuditEntryNotFoundError


class TestRemoveAuditTagHandler:
    def _make_handler(self):
        repo = MagicMock()
        handler = RemoveAuditTagHandler(repo=repo)
        return handler, repo

    def test_removes_tag_successfully(self):
        handler, repo = self._make_handler()
        repo.find_by_id.return_value = AuditEntry(
            id="entry1", company_id="c1", actor_id="a1",
            actor_email="a@b.com", action="test", resource_type="test",
            resource_id=None, http_method="POST", http_path="/test",
            ip_address=None, user_agent=None, request_data=None,
            response_status=200, changes=None, hash="abc",
        )

        handler.handle(
            RemoveAuditTagCommand(
                tag_id="tag1", entry_id="entry1", company_id="c1",
            )
        )

        repo.delete_tag.assert_called_once_with("tag1")

    def test_rejects_entry_not_found(self):
        handler, repo = self._make_handler()
        repo.find_by_id.return_value = None

        with pytest.raises(AuditEntryNotFoundError):
            handler.handle(
                RemoveAuditTagCommand(
                    tag_id="tag1", entry_id="missing", company_id="c1",
                )
            )
