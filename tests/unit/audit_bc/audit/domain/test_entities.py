from datetime import datetime, timezone

import pytest

from src.audit_bc.audit.domain.entities import (
    AuditEntry,
    AuditEntryTag,
    ComplianceControl,
    GdprRequest,
    RetentionPolicy,
)
from src.audit_bc.audit.domain.enums import (
    GdprRequestStatus,
    GdprRequestType,
)
from src.audit_bc.audit.domain.exceptions import (
    InvalidGdprStatusTransitionError,
    InvalidRetentionPeriodError,
)


class TestAuditEntryCreate:
    def test_create_audit_entry(self):
        entry = AuditEntry.create(
            company_id="01COMPANY000000000000000001",
            actor_id="01ACTOR00000000000000000001",
            actor_email="admin@example.com",
            action="asset.created",
            resource_type="asset",
            resource_id="01ASSET00000000000000000001",
            http_method="POST",
            http_path="/api/v1/assets",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_data={"name": "Laptop"},
            response_status=201,
            changes=None,
        )

        assert entry.id is not None
        assert len(entry.id) == 26
        assert entry.company_id == "01COMPANY000000000000000001"
        assert entry.actor_id == "01ACTOR00000000000000000001"
        assert entry.actor_email == "admin@example.com"
        assert entry.action == "asset.created"
        assert entry.resource_type == "asset"
        assert entry.resource_id == "01ASSET00000000000000000001"
        assert entry.http_method == "POST"
        assert entry.http_path == "/api/v1/assets"
        assert entry.ip_address == "192.168.1.1"
        assert entry.user_agent == "Mozilla/5.0"
        assert entry.request_data == {"name": "Laptop"}
        assert entry.response_status == 201
        assert entry.changes is None
        assert entry.hash is not None
        assert len(entry.hash) == 64  # SHA-256 hex digest
        assert entry.created_at is not None

    def test_create_audit_entry_with_nulls(self):
        entry = AuditEntry.create(
            company_id=None,
            actor_id=None,
            actor_email="",
            action="auth.register",
            resource_type="user",
            resource_id=None,
            http_method="POST",
            http_path="/api/v1/auth/register",
            ip_address=None,
            user_agent=None,
            request_data=None,
            response_status=201,
        )

        assert entry.company_id is None
        assert entry.actor_id is None
        assert entry.actor_email == ""
        assert entry.resource_id is None
        assert entry.ip_address is None
        assert entry.user_agent is None
        assert entry.request_data is None
        assert entry.hash is not None

    def test_create_generates_ulid(self):
        entry1 = AuditEntry.create(
            company_id="01COMPANY000000000000000001",
            actor_id="01ACTOR00000000000000000001",
            actor_email="a@b.com",
            action="test",
            resource_type="test",
            resource_id=None,
            http_method="POST",
            http_path="/test",
            ip_address=None,
            user_agent=None,
            request_data=None,
            response_status=200,
        )
        entry2 = AuditEntry.create(
            company_id="01COMPANY000000000000000001",
            actor_id="01ACTOR00000000000000000001",
            actor_email="a@b.com",
            action="test",
            resource_type="test",
            resource_id=None,
            http_method="POST",
            http_path="/test",
            ip_address=None,
            user_agent=None,
            request_data=None,
            response_status=200,
        )
        assert entry1.id != entry2.id

    def test_create_sets_created_at(self):
        before = datetime.now(timezone.utc)
        entry = AuditEntry.create(
            company_id="01COMPANY000000000000000001",
            actor_id="01ACTOR00000000000000000001",
            actor_email="a@b.com",
            action="test",
            resource_type="test",
            resource_id=None,
            http_method="POST",
            http_path="/test",
            ip_address=None,
            user_agent=None,
            request_data=None,
            response_status=200,
        )
        after = datetime.now(timezone.utc)
        assert before <= entry.created_at <= after


class TestComputeHash:
    def test_compute_hash_consistency(self):
        ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        h1 = AuditEntry.compute_hash(
            company_id="c1",
            actor_id="a1",
            action="asset.created",
            resource_type="asset",
            resource_id="r1",
            created_at=ts,
        )
        h2 = AuditEntry.compute_hash(
            company_id="c1",
            actor_id="a1",
            action="asset.created",
            resource_type="asset",
            resource_id="r1",
            created_at=ts,
        )
        assert h1 == h2
        assert len(h1) == 64

    def test_compute_hash_changes_with_different_input(self):
        ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        h1 = AuditEntry.compute_hash(
            company_id="c1",
            actor_id="a1",
            action="asset.created",
            resource_type="asset",
            resource_id="r1",
            created_at=ts,
        )
        h2 = AuditEntry.compute_hash(
            company_id="c1",
            actor_id="a1",
            action="asset.updated",
            resource_type="asset",
            resource_id="r1",
            created_at=ts,
        )
        assert h1 != h2

    def test_compute_hash_with_none_values(self):
        ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        h = AuditEntry.compute_hash(
            company_id=None,
            actor_id=None,
            action="auth.register",
            resource_type="user",
            resource_id=None,
            created_at=ts,
        )
        assert len(h) == 64


class TestComplianceControlCreate:
    def test_create_custom_control(self):
        control = ComplianceControl.create(
            company_id="c1",
            code="CUSTOM-001",
            name="Custom Control",
            framework="CUSTOM",
            description="A custom control",
        )
        assert control.id is not None
        assert len(control.id) == 26
        assert control.company_id == "c1"
        assert control.code == "CUSTOM-001"
        assert control.name == "Custom Control"
        assert control.framework == "CUSTOM"
        assert control.description == "A custom control"
        assert control.is_predefined is False
        assert control.is_active is True
        assert control.created_at is not None

    def test_create_predefined_control(self):
        control = ComplianceControl.create(
            company_id=None,
            code="NIS2-ART21-2A",
            name="Risk analysis",
            framework="NIS2",
            is_predefined=True,
        )
        assert control.company_id is None
        assert control.is_predefined is True
        assert control.description is None

    def test_create_generates_unique_ids(self):
        c1 = ComplianceControl.create(
            company_id="c1", code="A", name="A", framework="X"
        )
        c2 = ComplianceControl.create(
            company_id="c1", code="B", name="B", framework="X"
        )
        assert c1.id != c2.id


class TestAuditEntryTagCreate:
    def test_create_tag(self):
        tag = AuditEntryTag.create(
            audit_entry_id="entry1",
            control_id="ctrl1",
            tagged_by="user1",
        )
        assert tag.id is not None
        assert len(tag.id) == 26
        assert tag.audit_entry_id == "entry1"
        assert tag.control_id == "ctrl1"
        assert tag.tagged_by == "user1"
        assert tag.tagged_at is not None

    def test_create_generates_unique_ids(self):
        t1 = AuditEntryTag.create(
            audit_entry_id="e1", control_id="c1", tagged_by="u1"
        )
        t2 = AuditEntryTag.create(
            audit_entry_id="e1", control_id="c2", tagged_by="u1"
        )
        assert t1.id != t2.id


class TestRetentionPolicyCreate:
    def test_create_default(self):
        policy = RetentionPolicy.create(
            company_id="c1", updated_by="admin1"
        )
        assert policy.id is not None
        assert len(policy.id) == 26
        assert policy.company_id == "c1"
        assert policy.retention_months == 36
        assert policy.updated_by == "admin1"
        assert policy.updated_at is not None

    def test_create_custom_retention(self):
        policy = RetentionPolicy.create(
            company_id="c1",
            retention_months=84,
            updated_by="admin1",
        )
        assert policy.retention_months == 84

    def test_create_indefinite(self):
        policy = RetentionPolicy.create(
            company_id="c1",
            retention_months=0,
            updated_by="admin1",
        )
        assert policy.retention_months == 0

    def test_create_invalid_raises(self):
        with pytest.raises(InvalidRetentionPeriodError):
            RetentionPolicy.create(
                company_id="c1",
                retention_months=15,
                updated_by="admin1",
            )

    def test_create_generates_unique_ids(self):
        p1 = RetentionPolicy.create(
            company_id="c1", updated_by="admin1"
        )
        p2 = RetentionPolicy.create(
            company_id="c1", updated_by="admin1"
        )
        assert p1.id != p2.id


class TestGdprRequestCreate:
    def test_create_export_request(self):
        req = GdprRequest.create(
            company_id="c1",
            target_user_id="u1",
            target_user_email="user@example.com",
            requested_by="admin1",
            request_type=GdprRequestType.EXPORT,
        )
        assert req.id is not None
        assert len(req.id) == 26
        assert req.company_id == "c1"
        assert req.target_user_id == "u1"
        assert req.target_user_email == "user@example.com"
        assert req.requested_by == "admin1"
        assert req.request_type == GdprRequestType.EXPORT
        assert req.status == GdprRequestStatus.PENDING
        assert req.reason is None
        assert req.storage_key is None
        assert req.error_message is None
        assert req.started_at is None
        assert req.completed_at is None
        assert req.created_at is not None

    def test_create_anonymize_request_with_reason(self):
        req = GdprRequest.create(
            company_id="c1",
            target_user_id="u1",
            target_user_email="user@example.com",
            requested_by="admin1",
            request_type=GdprRequestType.ANONYMIZE,
            reason="User requested data deletion",
        )
        assert req.request_type == GdprRequestType.ANONYMIZE
        assert req.reason == "User requested data deletion"

    def test_create_generates_unique_ids(self):
        r1 = GdprRequest.create(
            company_id="c1",
            target_user_id="u1",
            target_user_email="a@b.com",
            requested_by="admin1",
            request_type=GdprRequestType.EXPORT,
        )
        r2 = GdprRequest.create(
            company_id="c1",
            target_user_id="u1",
            target_user_email="a@b.com",
            requested_by="admin1",
            request_type=GdprRequestType.EXPORT,
        )
        assert r1.id != r2.id


class TestGdprRequestStateMachine:
    def _make_pending_request(self):
        return GdprRequest.create(
            company_id="c1",
            target_user_id="u1",
            target_user_email="user@example.com",
            requested_by="admin1",
            request_type=GdprRequestType.EXPORT,
        )

    def test_start_processing(self):
        req = self._make_pending_request()
        req.start_processing()
        assert req.status == GdprRequestStatus.PROCESSING
        assert req.started_at is not None

    def test_complete_from_processing(self):
        req = self._make_pending_request()
        req.start_processing()
        req.complete(storage_key="exports/test.zip")
        assert req.status == GdprRequestStatus.COMPLETED
        assert req.storage_key == "exports/test.zip"
        assert req.completed_at is not None

    def test_complete_without_storage_key(self):
        req = self._make_pending_request()
        req.start_processing()
        req.complete()
        assert req.status == GdprRequestStatus.COMPLETED
        assert req.storage_key is None

    def test_fail_from_processing(self):
        req = self._make_pending_request()
        req.start_processing()
        req.fail("Something went wrong")
        assert req.status == GdprRequestStatus.FAILED
        assert req.error_message == "Something went wrong"
        assert req.completed_at is not None

    def test_cancel_from_pending(self):
        req = self._make_pending_request()
        req.cancel()
        assert req.status == GdprRequestStatus.CANCELLED

    def test_cannot_start_processing_from_processing(self):
        req = self._make_pending_request()
        req.start_processing()
        with pytest.raises(InvalidGdprStatusTransitionError):
            req.start_processing()

    def test_cannot_complete_from_pending(self):
        req = self._make_pending_request()
        with pytest.raises(InvalidGdprStatusTransitionError):
            req.complete()

    def test_cannot_fail_from_pending(self):
        req = self._make_pending_request()
        with pytest.raises(InvalidGdprStatusTransitionError):
            req.fail("error")

    def test_cannot_cancel_from_processing(self):
        req = self._make_pending_request()
        req.start_processing()
        with pytest.raises(InvalidGdprStatusTransitionError):
            req.cancel()

    def test_cannot_cancel_from_completed(self):
        req = self._make_pending_request()
        req.start_processing()
        req.complete()
        with pytest.raises(InvalidGdprStatusTransitionError):
            req.cancel()

    def test_cannot_cancel_from_failed(self):
        req = self._make_pending_request()
        req.start_processing()
        req.fail("error")
        with pytest.raises(InvalidGdprStatusTransitionError):
            req.cancel()
