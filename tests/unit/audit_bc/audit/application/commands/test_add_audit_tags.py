from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.commands.add_audit_tags import (
    AddAuditTagsCommand,
    AddAuditTagsHandler,
)
from src.audit_bc.audit.domain.entities import (
    AuditEntry,
    AuditEntryTag,
    ComplianceControl,
)
from src.audit_bc.audit.domain.exceptions import (
    AuditEntryNotFoundError,
    ControlNotFoundError,
)


def _make_entry():
    return AuditEntry(
        id="entry1", company_id="c1", actor_id="a1",
        actor_email="a@b.com", action="test", resource_type="test",
        resource_id=None, http_method="POST", http_path="/test",
        ip_address=None, user_agent=None, request_data=None,
        response_status=200, changes=None, hash="abc",
    )


def _make_control(control_id="ctrl1"):
    return ComplianceControl(
        id=control_id, company_id="c1", code="C1",
        name="Control", framework="X", description=None,
        is_predefined=False, is_active=True,
    )


class TestAddAuditTagsHandler:
    def _make_handler(self):
        repo = MagicMock()
        handler = AddAuditTagsHandler(repo=repo)
        return handler, repo

    def test_adds_tags_successfully(self):
        handler, repo = self._make_handler()
        repo.find_by_id.return_value = _make_entry()
        repo.find_tags_by_entry.return_value = []
        repo.find_control_by_id.return_value = _make_control()

        handler.handle(
            AddAuditTagsCommand(
                entry_id="entry1", company_id="c1",
                control_ids=["ctrl1", "ctrl2"], tagged_by="user1",
            )
        )

        assert repo.save_tag.call_count == 2

    def test_skips_duplicate_tags(self):
        handler, repo = self._make_handler()
        repo.find_by_id.return_value = _make_entry()
        repo.find_tags_by_entry.return_value = [
            AuditEntryTag(
                id="t1", audit_entry_id="entry1",
                control_id="ctrl1", tagged_by="user1",
            )
        ]
        repo.find_control_by_id.return_value = _make_control("ctrl2")

        handler.handle(
            AddAuditTagsCommand(
                entry_id="entry1", company_id="c1",
                control_ids=["ctrl1", "ctrl2"], tagged_by="user1",
            )
        )

        # Only ctrl2 should be saved (ctrl1 already exists)
        assert repo.save_tag.call_count == 1

    def test_rejects_entry_not_found(self):
        handler, repo = self._make_handler()
        repo.find_by_id.return_value = None

        with pytest.raises(AuditEntryNotFoundError):
            handler.handle(
                AddAuditTagsCommand(
                    entry_id="missing", company_id="c1",
                    control_ids=["ctrl1"], tagged_by="user1",
                )
            )

    def test_rejects_control_not_found(self):
        handler, repo = self._make_handler()
        repo.find_by_id.return_value = _make_entry()
        repo.find_tags_by_entry.return_value = []
        repo.find_control_by_id.return_value = None

        with pytest.raises(ControlNotFoundError):
            handler.handle(
                AddAuditTagsCommand(
                    entry_id="entry1", company_id="c1",
                    control_ids=["missing"], tagged_by="user1",
                )
            )
