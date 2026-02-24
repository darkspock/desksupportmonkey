from unittest.mock import MagicMock

from src.audit_bc.audit.application.services.audit_service import AuditService
from src.audit_bc.audit.domain.entities import AuditEntry


class TestAuditService:
    def _make_service(self):
        repo = MagicMock()
        service = AuditService(repository=repo)
        return service, repo

    def test_record_creates_entry(self):
        service, repo = self._make_service()

        service.record(
            company_id="c1",
            actor_id="a1",
            actor_email="admin@example.com",
            action="asset.created",
            resource_type="asset",
            resource_id="r1",
            http_method="POST",
            http_path="/api/v1/assets",
            ip_address="1.2.3.4",
            user_agent="Mozilla",
            request_data={"name": "Laptop"},
            response_status=201,
        )

        repo.save.assert_called_once()
        saved_entry = repo.save.call_args[0][0]
        assert isinstance(saved_entry, AuditEntry)
        assert saved_entry.company_id == "c1"
        assert saved_entry.actor_id == "a1"
        assert saved_entry.action == "asset.created"
        assert saved_entry.response_status == 201

    def test_record_sanitizes_request_data(self):
        service, repo = self._make_service()

        service.record(
            company_id="c1",
            actor_id="a1",
            actor_email="admin@example.com",
            action="user.updated",
            resource_type="user",
            resource_id="u1",
            http_method="PUT",
            http_path="/api/v1/users/u1",
            ip_address=None,
            user_agent=None,
            request_data={"name": "John", "password": "secret"},
            response_status=200,
        )

        saved_entry = repo.save.call_args[0][0]
        assert saved_entry.request_data["name"] == "John"
        assert saved_entry.request_data["password"] == "[REDACTED]"

    def test_record_with_no_actor(self):
        service, repo = self._make_service()

        service.record(
            company_id=None,
            actor_id=None,
            actor_email="",
            action="auth.register",
            resource_type="user",
            resource_id=None,
            http_method="POST",
            http_path="/api/v1/auth/register",
            ip_address="1.2.3.4",
            user_agent=None,
            request_data=None,
            response_status=201,
        )

        saved_entry = repo.save.call_args[0][0]
        assert saved_entry.company_id is None
        assert saved_entry.actor_id is None
        assert saved_entry.actor_email == ""
        assert saved_entry.request_data is None

    def test_record_with_changes(self):
        service, repo = self._make_service()
        changes = {"status": {"old": "open", "new": "closed"}}

        service.record(
            company_id="c1",
            actor_id="a1",
            actor_email="admin@example.com",
            action="request.updated",
            resource_type="request",
            resource_id="r1",
            http_method="PATCH",
            http_path="/api/v1/requests/r1",
            ip_address=None,
            user_agent=None,
            request_data=None,
            response_status=200,
            changes=changes,
        )

        saved_entry = repo.save.call_args[0][0]
        assert saved_entry.changes == changes
