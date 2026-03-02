"""Integration tests for /api/v1/requests endpoints (mixed auth)."""

import pytest


def _create_request(client, title="Test Request", req_type="incident"):
    resp = client.post("/api/v1/requests", json={
        "type": req_type,
        "title": title,
        "description": "Test description for integration test",
    })
    return resp


class TestCreateRequestSubtype:
    def test_create_with_valid_subtype(self, client, auth_as, employee_user):
        auth_as(employee_user)

        resp = client.post("/api/v1/requests", json={
            "type": "repair",
            "title": "Broken keyboard",
            "description": "Keys are stuck",
            "subtype": "hardware",
        })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["subtype"] == "hardware"
        assert data["type"] == "repair"

    def test_create_with_invalid_subtype_returns_422(self, client, auth_as, employee_user):
        auth_as(employee_user)

        resp = client.post("/api/v1/requests", json={
            "type": "repair",
            "title": "Broken keyboard",
            "description": "Keys are stuck",
            "subtype": "vpn",  # vpn is not valid for repair
        })

        assert resp.status_code == 422

    def test_create_without_subtype_backward_compatible(self, client, auth_as, employee_user):
        auth_as(employee_user)

        resp = client.post("/api/v1/requests", json={
            "type": "incident",
            "title": "System down",
            "description": "Cannot login",
        })

        assert resp.status_code == 201
        assert resp.json()["data"]["subtype"] is None

    def test_list_requests_filter_by_subtype(self, client, auth_as, employee_user, technician_user):
        auth_as(employee_user)
        # Create repair with hardware subtype
        client.post("/api/v1/requests", json={
            "type": "repair", "title": "Hardware repair",
            "description": "Broken keyboard", "subtype": "hardware",
        })
        # Create repair with software subtype
        client.post("/api/v1/requests", json={
            "type": "repair", "title": "Software repair",
            "description": "App crash", "subtype": "software",
        })

        auth_as(technician_user)
        resp = client.get("/api/v1/requests?subtype=hardware")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert all(r["subtype"] == "hardware" for r in data)


class TestCreateRequestPriorityScoring:
    def test_create_request_priority_from_scorer(self, client, auth_as, employee_user):
        """Priority is computed by scorer, not hardcoded default."""
        auth_as(employee_user)

        resp = client.post("/api/v1/requests", json={
            "type": "incident",
            "title": "System down",
            "description": "Cannot login",
        })

        assert resp.status_code == 201
        data = resp.json()["data"]
        # incident + no subtype + no dept boost + employee = score 2 → medium
        assert data["priority"] == "medium"
        assert "priority_scoring" in data["data"]
        assert data["data"]["priority_scoring"]["type_weight"] == 2

    def test_create_request_scoring_breakdown_in_response(self, client, auth_as, employee_user):
        auth_as(employee_user)

        resp = client.post("/api/v1/requests", json={
            "type": "repair",
            "title": "Broken keyboard",
            "description": "Keys are stuck",
            "subtype": "hardware",
        })

        assert resp.status_code == 201
        data = resp.json()["data"]
        scoring = data["data"]["priority_scoring"]
        assert scoring["type_weight"] == 1   # repair
        assert scoring["subtype_weight"] == 1  # hardware
        assert scoring["raw_score"] == 2  # no dept boost, no admin


class TestCreateRequest:
    def test_create_request_as_employee(self, client, auth_as, employee_user):
        auth_as(employee_user)

        resp = _create_request(client, title="My laptop is broken")

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["title"] == "My laptop is broken"
        assert data["status"] == "submitted"
        assert data["type"] == "incident"
        assert data["priority"] == "medium"  # incident(2) + employee(0) = 2 → medium

    def test_create_request_as_technician(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = _create_request(client, title="Equipment request", req_type="new_equipment")

        assert resp.status_code == 201
        assert resp.json()["data"]["priority"] == "low"  # default for new_equipment


class TestListRequests:
    def test_list_requests(self, client, auth_as, technician_user, employee_user):
        # Create a request as employee
        auth_as(employee_user)
        _create_request(client)

        # List as technician
        auth_as(technician_user)
        resp = client.get("/api/v1/requests")

        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1

    def test_list_requests_filter_by_status(self, client, auth_as, technician_user, employee_user):
        auth_as(employee_user)
        _create_request(client)

        auth_as(technician_user)
        resp = client.get("/api/v1/requests?status=submitted")

        assert resp.status_code == 200
        for r in resp.json()["data"]:
            assert r["status"] == "submitted"


class TestGetRequest:
    def test_get_request_as_owner(self, client, auth_as, employee_user):
        auth_as(employee_user)
        create_resp = _create_request(client)
        req_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/requests/{req_id}")

        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == req_id

    def test_get_request_as_technician(self, client, auth_as, employee_user, technician_user):
        auth_as(employee_user)
        create_resp = _create_request(client)
        req_id = create_resp.json()["data"]["id"]

        auth_as(technician_user)
        resp = client.get(f"/api/v1/requests/{req_id}")

        assert resp.status_code == 200

    def test_employee_cannot_see_others_request(self, client, auth_as, employee_user, make_user, company):
        from src.auth_bc.user.domain.enums import UserRole

        auth_as(employee_user)
        create_resp = _create_request(client)
        req_id = create_resp.json()["data"]["id"]

        other_employee = make_user("other@testco.com", role=UserRole.EMPLOYEE, company_id=company.id)
        auth_as(other_employee)
        resp = client.get(f"/api/v1/requests/{req_id}")

        assert resp.status_code == 404

    def test_get_request_not_found(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.get("/api/v1/requests/nonexistent")

        assert resp.status_code == 404


class TestRequestEvents:
    def test_list_events_as_owner(self, client, auth_as, employee_user):
        auth_as(employee_user)
        create_resp = _create_request(client, title="History request")
        req_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/requests/{req_id}/events")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        assert any(e["event_type"] == "created" for e in data)

    def test_list_events_includes_status_changed(self, client, auth_as, employee_user, technician_user):
        auth_as(employee_user)
        create_resp = _create_request(client, title="Status history request")
        req_id = create_resp.json()["data"]["id"]

        auth_as(technician_user)
        status_resp = client.patch(f"/api/v1/requests/{req_id}/status", json={"status": "in_review"})
        assert status_resp.status_code == 200

        resp = client.get(f"/api/v1/requests/{req_id}/events")
        assert resp.status_code == 200

        status_events = [e for e in resp.json()["data"] if e["event_type"] == "status_changed"]
        assert status_events
        first = status_events[0]
        assert first["data"]["old_status"] == "submitted"
        assert first["data"]["new_status"] == "in_review"


class TestChangeRequestStatus:
    def test_change_status(self, client, auth_as, employee_user, technician_user):
        auth_as(employee_user)
        create_resp = _create_request(client)
        req_id = create_resp.json()["data"]["id"]

        auth_as(technician_user)
        resp = client.patch(f"/api/v1/requests/{req_id}/status", json={"status": "in_review"})

        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "in_review"

    def test_invalid_status_transition(self, client, auth_as, employee_user, technician_user):
        """submitted -> resolved is invalid (must go through in_review first)."""
        auth_as(employee_user)
        create_resp = _create_request(client)
        req_id = create_resp.json()["data"]["id"]

        auth_as(technician_user)
        resp = client.patch(f"/api/v1/requests/{req_id}/status", json={"status": "resolved"})

        assert resp.status_code == 409


class TestChangeRequestPriority:
    def test_change_priority(self, client, auth_as, employee_user, technician_user):
        auth_as(employee_user)
        create_resp = _create_request(client)
        req_id = create_resp.json()["data"]["id"]

        auth_as(technician_user)
        resp = client.patch(f"/api/v1/requests/{req_id}/priority", json={"priority": "urgent"})

        assert resp.status_code == 200
        assert resp.json()["data"]["priority"] == "urgent"


class TestAssignRequest:
    def test_assign_request(self, client, auth_as, employee_user, technician_user):
        auth_as(employee_user)
        create_resp = _create_request(client)
        req_id = create_resp.json()["data"]["id"]

        auth_as(technician_user)
        resp = client.patch(f"/api/v1/requests/{req_id}/assign", json={"user_id": technician_user.id})

        assert resp.status_code == 200
        assert resp.json()["data"]["assigned_to"] == technician_user.id

    def test_assign_nonexistent_user(self, client, auth_as, employee_user, technician_user):
        auth_as(employee_user)
        create_resp = _create_request(client)
        req_id = create_resp.json()["data"]["id"]

        auth_as(technician_user)
        resp = client.patch(f"/api/v1/requests/{req_id}/assign", json={"user_id": "nonexistent"})

        assert resp.status_code == 404


class TestComments:
    def test_add_comment(self, client, auth_as, employee_user):
        auth_as(employee_user)
        create_resp = _create_request(client)
        req_id = create_resp.json()["data"]["id"]

        resp = client.post(f"/api/v1/requests/{req_id}/comments", json={"body": "This is urgent!"})

        assert resp.status_code == 201
        assert resp.json()["data"]["body"] == "This is urgent!"

    def test_list_comments(self, client, auth_as, employee_user):
        auth_as(employee_user)
        create_resp = _create_request(client)
        req_id = create_resp.json()["data"]["id"]
        client.post(f"/api/v1/requests/{req_id}/comments", json={"body": "Comment 1"})
        client.post(f"/api/v1/requests/{req_id}/comments", json={"body": "Comment 2"})

        resp = client.get(f"/api/v1/requests/{req_id}/comments")

        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2


class TestCreateRequestAIClassification:
    def test_create_without_config_no_ai_metadata(self, client, auth_as, employee_user, monkeypatch):
        """When no classification config exists, no ai_classification in data."""
        from core.config import settings

        monkeypatch.setattr(settings.ai, "GROQ_API_KEY", "")
        auth_as(employee_user)

        resp = client.post("/api/v1/requests", json={
            "type": "incident",
            "title": "System down",
            "description": "Cannot login",
        })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert "ai_classification" not in (data.get("data") or {})

    def test_create_without_config_uses_groq_when_key_present(self, client, auth_as, employee_user, monkeypatch):
        """Without persisted config, runtime uses Groq defaults if GROQ_API_KEY exists."""
        from unittest.mock import patch
        from core.config import settings
        from src.request_bc.request.application.services.request_classifier import (
            ClassificationResult,
        )

        monkeypatch.setattr(settings.ai, "GROQ_API_KEY", "gsk-test-key")

        with patch(
            "src.request_bc.request.infrastructure.ai.groq_classifier.GroqRequestClassifier.classify",
            return_value=ClassificationResult(
                type="incident",
                subtype=None,
                priority_hint=1,
                confidence=0.9,
            ),
        ) as groq_classify:
            auth_as(employee_user)
            resp = client.post("/api/v1/requests", json={
                "type": "incident",
                "title": "System down",
                "description": "Cannot login",
            })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["data"]["ai_classification"]["provider"] == "groq"
        groq_classify.assert_called_once()

    def test_create_with_ai_enabled_includes_metadata(self, client, auth_as, employee_user, db_session):
        """When AI config enabled and classifier available, metadata stored."""
        from unittest.mock import MagicMock, patch
        from src.company_bc.classification_config.infrastructure.models import (
            ClassificationConfigModel,
        )
        from src.request_bc.request.application.services.classification_service import (
            ClassificationServiceResult,
        )
        import ulid

        # Insert classification config
        config_model = ClassificationConfigModel(
            id=str(ulid.new()),
            company_id=employee_user.company_id,
            is_enabled=True,
            provider="openai",
            model="gpt-4o-mini",
            confidence_threshold=0.7,
            prompt_template="Classify this request",
            timeout_seconds=5,
        )
        db_session.add(config_model)
        db_session.flush()

        mock_result = ClassificationServiceResult(
            resolved_type="incident",
            resolved_subtype=None,
            ai_priority_hint=1,
            ai_classification={"ai_used": True, "provider": "openai", "confidence": 0.9},
        )

        with patch(
            "adapters.http.api.requests.routers.ClassificationService"
        ) as MockCls:
            mock_svc = MagicMock()
            mock_svc.classify_request.return_value = mock_result
            MockCls.build_classifier.return_value = MagicMock()
            MockCls.return_value = mock_svc

            auth_as(employee_user)
            resp = client.post("/api/v1/requests", json={
                "type": "incident",
                "title": "System down",
                "description": "Cannot login",
            })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert "ai_classification" in data["data"]
        assert data["data"]["ai_classification"]["ai_used"] is True

    def test_create_with_ai_override_changes_type(self, client, auth_as, employee_user, db_session):
        """AI override changes the resolved type/subtype."""
        from unittest.mock import MagicMock, patch
        from src.company_bc.classification_config.infrastructure.models import (
            ClassificationConfigModel,
        )
        from src.request_bc.request.application.services.classification_service import (
            ClassificationServiceResult,
        )
        import ulid

        config_model = ClassificationConfigModel(
            id=str(ulid.new()),
            company_id=employee_user.company_id,
            is_enabled=True,
            provider="openai",
            model="gpt-4o-mini",
            confidence_threshold=0.7,
            prompt_template="Classify this request",
            timeout_seconds=5,
        )
        db_session.add(config_model)
        db_session.flush()

        mock_result = ClassificationServiceResult(
            resolved_type="configuration",
            resolved_subtype="account_setup",
            ai_priority_hint=0,
            ai_classification={
                "ai_used": True, "provider": "openai", "confidence": 0.95,
                "override_applied": True,
                "user_original": {"type": "incident", "subtype": None},
            },
        )

        with patch(
            "adapters.http.api.requests.routers.ClassificationService"
        ) as MockCls:
            mock_svc = MagicMock()
            mock_svc.classify_request.return_value = mock_result
            MockCls.build_classifier.return_value = MagicMock()
            MockCls.return_value = mock_svc

            auth_as(employee_user)
            resp = client.post("/api/v1/requests", json={
                "type": "incident",
                "title": "Setup email",
                "description": "Need email configured",
            })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["type"] == "configuration"
        assert data["subtype"] == "account_setup"
        assert data["data"]["ai_classification"]["override_applied"] is True
        assert data["data"]["ai_classification"]["user_original"]["type"] == "incident"

    def test_create_with_groq_key_forces_groq_runtime(self, client, auth_as, employee_user, db_session, monkeypatch):
        """With GROQ_API_KEY present, runtime provider is forced to groq."""
        from unittest.mock import patch
        from core.config import settings
        from src.company_bc.classification_config.infrastructure.models import (
            ClassificationConfigModel,
        )
        from src.request_bc.request.application.services.request_classifier import (
            ClassificationResult,
        )
        import ulid

        config_model = ClassificationConfigModel(
            id=str(ulid.new()),
            company_id=employee_user.company_id,
            is_enabled=True,
            provider="openai",
            model="gpt-4o-mini",
            confidence_threshold=0.7,
            prompt_template="Classify this request",
            timeout_seconds=5,
        )
        db_session.add(config_model)
        db_session.flush()

        monkeypatch.setattr(settings.ai, "GROQ_API_KEY", "gsk-test-key")

        with patch(
            "src.request_bc.request.infrastructure.ai.groq_classifier.GroqRequestClassifier.classify",
            return_value=ClassificationResult(
                type="incident",
                subtype=None,
                priority_hint=1,
                confidence=0.9,
            ),
        ) as groq_classify:
            auth_as(employee_user)
            resp = client.post("/api/v1/requests", json={
                "type": "incident",
                "title": "System down",
                "description": "Cannot login",
            })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["data"]["ai_classification"]["provider"] == "groq"
        groq_classify.assert_called_once()


class TestNotes:
    def test_add_note(self, client, auth_as, employee_user, technician_user):
        auth_as(employee_user)
        create_resp = _create_request(client)
        req_id = create_resp.json()["data"]["id"]

        auth_as(technician_user)
        resp = client.post(f"/api/v1/requests/{req_id}/notes", json={"body": "Internal note"})

        assert resp.status_code == 201
        assert resp.json()["data"]["body"] == "Internal note"

    def test_list_notes(self, client, auth_as, employee_user, technician_user):
        auth_as(employee_user)
        create_resp = _create_request(client)
        req_id = create_resp.json()["data"]["id"]

        auth_as(technician_user)
        client.post(f"/api/v1/requests/{req_id}/notes", json={"body": "Note 1"})
        client.post(f"/api/v1/requests/{req_id}/notes", json={"body": "Note 2"})

        resp = client.get(f"/api/v1/requests/{req_id}/notes")

        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2


# ── E53-F1: Waiting for employee status ────────────────────────

def _advance_to_in_progress(client, auth_as, employee_user, technician_user):
    """Helper: create a request and advance it to in_progress."""
    auth_as(employee_user)
    create_resp = _create_request(client, title="Waiting test")
    req_id = create_resp.json()["data"]["id"]

    auth_as(technician_user)
    client.patch(f"/api/v1/requests/{req_id}/status", json={"status": "in_review"})
    client.patch(f"/api/v1/requests/{req_id}/status", json={"status": "in_progress"})
    return req_id


class TestWaitingForEmployeeStatus:
    def test_transition_to_waiting_for_employee(self, client, auth_as, employee_user, technician_user):
        req_id = _advance_to_in_progress(client, auth_as, employee_user, technician_user)

        resp = client.patch(f"/api/v1/requests/{req_id}/status", json={"status": "waiting_for_employee"})

        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "waiting_for_employee"

    def test_invalid_transition_submitted_to_waiting(self, client, auth_as, employee_user, technician_user):
        auth_as(employee_user)
        create_resp = _create_request(client, title="Invalid transition test")
        req_id = create_resp.json()["data"]["id"]

        auth_as(technician_user)
        resp = client.patch(f"/api/v1/requests/{req_id}/status", json={"status": "waiting_for_employee"})

        assert resp.status_code == 409

    def test_comment_auto_transitions_from_waiting(self, client, auth_as, employee_user, technician_user):
        req_id = _advance_to_in_progress(client, auth_as, employee_user, technician_user)
        client.patch(f"/api/v1/requests/{req_id}/status", json={"status": "waiting_for_employee"})

        # Employee adds a comment
        auth_as(employee_user)
        resp = client.post(f"/api/v1/requests/{req_id}/comments", json={"body": "Here is the info"})
        assert resp.status_code == 201

        # Verify status auto-transitioned
        auth_as(technician_user)
        get_resp = client.get(f"/api/v1/requests/{req_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["status"] == "in_progress"

    def test_filter_by_waiting_for_employee(self, client, auth_as, employee_user, technician_user):
        req_id = _advance_to_in_progress(client, auth_as, employee_user, technician_user)
        client.patch(f"/api/v1/requests/{req_id}/status", json={"status": "waiting_for_employee"})

        resp = client.get("/api/v1/requests?status=waiting_for_employee")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert any(r["id"] == req_id for r in data)
        assert all(r["status"] == "waiting_for_employee" for r in data)

    def test_auto_transition_creates_status_changed_event(self, client, auth_as, employee_user, technician_user):
        req_id = _advance_to_in_progress(client, auth_as, employee_user, technician_user)
        client.patch(f"/api/v1/requests/{req_id}/status", json={"status": "waiting_for_employee"})

        auth_as(employee_user)
        client.post(f"/api/v1/requests/{req_id}/comments", json={"body": "Replying"})

        auth_as(technician_user)
        events_resp = client.get(f"/api/v1/requests/{req_id}/events")
        assert events_resp.status_code == 200
        events = events_resp.json()["data"]
        auto_events = [
            e for e in events
            if e["event_type"] == "status_changed"
            and (e.get("data") or {}).get("old_status") == "waiting_for_employee"
            and (e.get("data") or {}).get("new_status") == "in_progress"
        ]
        assert len(auto_events) >= 1


class TestEmailNotifications:
    @pytest.fixture(autouse=True)
    def _email_bus(self, client):
        """Override the no-op EventBus with one that has EmailSubscriber registered."""
        from adapters.http.api.dependencies import get_event_bus
        from src.notification_bc.notification.application.services.event_bus import EventBus
        from src.notification_bc.notification.application.services.email_subscriber import (
            EmailSubscriber,
        )

        bus = EventBus()
        bus.subscribe(EmailSubscriber())
        client.app.dependency_overrides[get_event_bus] = lambda: bus
        yield
        # Restore no-op bus so other tests are unaffected
        client.app.dependency_overrides[get_event_bus] = lambda: EventBus()

    def test_technician_comment_enqueues_email_for_employee(
        self, client, auth_as, employee_user, technician_user,
    ):
        """Technician comments on request -> email task enqueued for the employee."""
        auth_as(employee_user)
        create_resp = _create_request(client, title="Email test request")
        req_id = create_resp.json()["data"]["id"]

        auth_as(technician_user)
        client.patch(f"/api/v1/requests/{req_id}/assign", json={"user_id": technician_user.id})

        from unittest.mock import patch
        with patch(
            "core.tasks.email_notifications.send_request_notification_email.delay"
        ) as mock_delay:
            resp = client.post(
                f"/api/v1/requests/{req_id}/comments",
                json={"body": "Please provide more info"},
            )

            assert resp.status_code == 201
            mock_delay.assert_called_once()
            call_kwargs = mock_delay.call_args[1]
            assert call_kwargs["to_email"] == employee_user.email
            assert call_kwargs["variant"] == "comment"
            assert call_kwargs["comment_body"] == "Please provide more info"

    def test_waiting_status_enqueues_action_required_email(
        self, client, auth_as, employee_user, technician_user,
    ):
        """Setting status to waiting_for_employee -> email task with action_required variant."""
        req_id = _advance_to_in_progress(client, auth_as, employee_user, technician_user)

        from unittest.mock import patch
        with patch(
            "core.tasks.email_notifications.send_request_notification_email.delay"
        ) as mock_delay:
            resp = client.patch(
                f"/api/v1/requests/{req_id}/status",
                json={"status": "waiting_for_employee"},
            )

            assert resp.status_code == 200
            # Find the action_required call (there may also be a notification subscriber call)
            action_calls = [
                c for c in mock_delay.call_args_list
                if c[1].get("variant") == "action_required"
            ]
            assert len(action_calls) == 1
            assert action_calls[0][1]["to_email"] == employee_user.email

    def test_employee_comment_no_technician_no_email(
        self, client, auth_as, employee_user,
    ):
        """Employee comments on unassigned request -> no email task enqueued."""
        auth_as(employee_user)
        create_resp = _create_request(client, title="Unassigned request")
        req_id = create_resp.json()["data"]["id"]

        from unittest.mock import patch
        with patch(
            "core.tasks.email_notifications.send_request_notification_email.delay"
        ) as mock_delay:
            resp = client.post(
                f"/api/v1/requests/{req_id}/comments",
                json={"body": "Any update?"},
            )

            assert resp.status_code == 201
            mock_delay.assert_not_called()


class TestCommentResponseEnrichment:
    def test_list_comments_includes_author_name_and_role(
        self, client, auth_as, employee_user,
    ):
        """GET comments returns author_name and author_role."""
        auth_as(employee_user)
        create_resp = _create_request(client, title="Enrichment test")
        req_id = create_resp.json()["data"]["id"]
        client.post(f"/api/v1/requests/{req_id}/comments", json={"body": "Test"})

        resp = client.get(f"/api/v1/requests/{req_id}/comments")
        assert resp.status_code == 200
        comment = resp.json()["data"][0]
        assert "author_name" in comment
        assert comment["author_role"] == "employee"

    def test_add_comment_returns_author_name_and_role(
        self, client, auth_as, employee_user,
    ):
        """POST comment returns author_name and author_role of current user."""
        auth_as(employee_user)
        create_resp = _create_request(client, title="Enrichment test")
        req_id = create_resp.json()["data"]["id"]

        resp = client.post(f"/api/v1/requests/{req_id}/comments", json={"body": "Test"})
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["author_role"] == "employee"
        assert "author_name" in data
