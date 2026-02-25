from unittest.mock import MagicMock

import pytest

from src.request_bc.request.application.commands.create_request import (
    CreateRequestCommand,
    CreateRequestCommandHandler,
)
from src.request_bc.request.application.commands.change_request_status import (
    ChangeRequestStatusCommand,
    ChangeRequestStatusCommandHandler,
    RequestNotFoundError as StatusNotFoundError,
)
from src.request_bc.request.application.commands.change_request_priority import (
    ChangeRequestPriorityCommand,
    ChangeRequestPriorityCommandHandler,
    RequestNotFoundError as PriorityNotFoundError,
)
from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.domain.enums import (
    InvalidStatusTransitionError,
    RequestType,
)


def _make_request(**overrides):
    defaults = dict(
        company_id="comp1",
        created_by="user1",
        type=RequestType.INCIDENT,
        title="Test request",
        description="Test description",
    )
    defaults.update(overrides)
    return ServiceRequest.create(**defaults)


def _make_repo(request=None):
    repo = MagicMock()
    repo.save.side_effect = lambda r: r
    repo.find_by_id.return_value = request
    return repo


class TestCreateRequestCommandScoring:
    def test_priority_comes_from_scorer_not_default(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        # incident with no dept boost, employee → score=2 → medium
        # (default would have been HIGH, but scorer returns MEDIUM here)
        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="incident", title="Test", description="Test description",
                department_priority_weight=0, user_role="employee",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.priority.value == "medium"  # scorer result (2 → medium)

    def test_scoring_breakdown_stored_in_data(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="incident", title="Test", description="Test description",
                department_priority_weight=0, user_role="employee",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.data is not None
        assert "priority_scoring" in saved.data
        breakdown = saved.data["priority_scoring"]
        assert "raw_score" in breakdown
        assert breakdown["type_weight"] == 2

    def test_create_without_dept_weight_uses_zero(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="new_equipment", title="Test", description="Test description",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.data["priority_scoring"]["department_weight"] == 0


class TestCreateRequestCommandSubtype:
    def test_create_with_valid_subtype(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="repair", title="Broken keyboard", description="Keys fell off",
                subtype="hardware",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.subtype == "hardware"

    def test_create_without_subtype_backward_compatible(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="incident", title="System down", description="Cannot login",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.subtype is None

    def test_create_new_types_work(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        for request_type in ("repair", "configuration", "access_request"):
            repo.reset_mock()
            handler.handle(
                CreateRequestCommand(
                    company_id="comp1", created_by="user1",
                    type=request_type, title="Test", description="Test description",
                )
            )
            assert repo.save.call_count == 1


class TestCreateRequestCommand:
    def test_success_incident_auto_priority(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1",
                created_by="user1",
                type="incident",
                title="Laptop broken",
                description="Screen cracked",
            )
        )

        assert repo.save.call_count == 1
        assert repo.save_event.call_count == 1
        event = repo.save_event.call_args[0][0]
        assert event.event_type == "created"

    def test_success_new_equipment_auto_priority(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1",
                created_by="user1",
                type="new_equipment",
                title="Need monitor",
                description="Second monitor",
            )
        )

        repo.save.assert_called_once()

    def test_success_with_data(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1",
                created_by="user1",
                type="incident",
                title="Laptop broken",
                description="Screen cracked",
                data={"asset_id": "asset123"},
            )
        )

        repo.save.assert_called_once()

    def test_free_form_type_accepted(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1",
                created_by="user1",
                type="Custom Workflow Type",
                title="Test",
                description="Test",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.type == "Custom Workflow Type"


class TestChangeRequestStatusCommand:
    def test_success(self):
        request = _make_request()
        repo = _make_repo(request)
        handler = ChangeRequestStatusCommandHandler(request_repo=repo)

        handler.handle(
            ChangeRequestStatusCommand(
                request_id=request.id,
                company_id="comp1",
                new_status="in_review",
                performed_by="tech1",
            )
        )

        repo.save.assert_called_once()
        assert repo.save_event.call_count >= 1

    def test_not_found_raises(self):
        repo = _make_repo(None)
        handler = ChangeRequestStatusCommandHandler(request_repo=repo)

        with pytest.raises(StatusNotFoundError):
            handler.handle(
                ChangeRequestStatusCommand(
                    request_id="bad",
                    company_id="comp1",
                    new_status="in_review",
                    performed_by="tech1",
                )
            )

    def test_invalid_transition_raises(self):
        request = _make_request()
        repo = _make_repo(request)
        handler = ChangeRequestStatusCommandHandler(request_repo=repo)

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                ChangeRequestStatusCommand(
                    request_id=request.id,
                    company_id="comp1",
                    new_status="resolved",
                    performed_by="tech1",
                )
            )

    def test_auto_assign_on_in_review(self):
        request = _make_request()
        assert request.assigned_to is None
        repo = _make_repo(request)
        handler = ChangeRequestStatusCommandHandler(request_repo=repo)

        handler.handle(
            ChangeRequestStatusCommand(
                request_id=request.id,
                company_id="comp1",
                new_status="in_review",
                performed_by="tech1",
            )
        )

        repo.save.assert_called_once()
        # Two events: status_changed + assigned
        assert repo.save_event.call_count == 2
        events = [call[0][0] for call in repo.save_event.call_args_list]
        assert events[0].event_type == "status_changed"
        assert events[1].event_type == "assigned"
        assert events[1].data["reason"] == "auto_assign_on_review"

    def test_no_auto_assign_if_already_assigned(self):
        request = _make_request()
        request.assign("other_tech")
        repo = _make_repo(request)
        handler = ChangeRequestStatusCommandHandler(request_repo=repo)

        handler.handle(
            ChangeRequestStatusCommand(
                request_id=request.id,
                company_id="comp1",
                new_status="in_review",
                performed_by="tech1",
            )
        )

        repo.save.assert_called_once()
        # Only one event: status_changed (no auto-assign)
        assert repo.save_event.call_count == 1


class TestChangeRequestPriorityCommand:
    def test_success(self):
        request = _make_request()
        repo = _make_repo(request)
        handler = ChangeRequestPriorityCommandHandler(request_repo=repo)

        handler.handle(
            ChangeRequestPriorityCommand(
                request_id=request.id,
                company_id="comp1",
                new_priority="urgent",
                performed_by="tech1",
            )
        )

        repo.save.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.event_type == "priority_changed"
        assert event.data["old_priority"] == "high"  # incident default
        assert event.data["new_priority"] == "urgent"

    def test_not_found_raises(self):
        repo = _make_repo(None)
        handler = ChangeRequestPriorityCommandHandler(request_repo=repo)

        with pytest.raises(PriorityNotFoundError):
            handler.handle(
                ChangeRequestPriorityCommand(
                    request_id="bad",
                    company_id="comp1",
                    new_priority="urgent",
                    performed_by="tech1",
                )
            )

    def test_invalid_priority_raises(self):
        request = _make_request()
        repo = _make_repo(request)
        handler = ChangeRequestPriorityCommandHandler(request_repo=repo)

        with pytest.raises(ValueError):
            handler.handle(
                ChangeRequestPriorityCommand(
                    request_id=request.id,
                    company_id="comp1",
                    new_priority="invalid",
                    performed_by="tech1",
                )
            )


class TestCreateRequestApprovalRouting:
    def test_new_equipment_with_manager_gets_pending_approval(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="new_equipment", title="New laptop", description="For work",
                department_has_manager=True,
            )
        )

        saved = repo.save.call_args[0][0]
        from src.request_bc.request.domain.enums import RequestStatus
        assert saved.status == RequestStatus.PENDING_APPROVAL

    def test_new_equipment_without_manager_gets_submitted(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="new_equipment", title="New laptop", description="For work",
                department_has_manager=False,
            )
        )

        saved = repo.save.call_args[0][0]
        from src.request_bc.request.domain.enums import RequestStatus
        assert saved.status == RequestStatus.SUBMITTED

    def test_incident_always_submitted_regardless_of_manager(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="incident", title="System down", description="Cannot access",
                department_has_manager=True,
            )
        )

        saved = repo.save.call_args[0][0]
        from src.request_bc.request.domain.enums import RequestStatus
        assert saved.status == RequestStatus.SUBMITTED

    def test_onboarding_always_submitted(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="onboarding", title="New hire setup", description="New employee",
                department_has_manager=True,
            )
        )

        saved = repo.save.call_args[0][0]
        from src.request_bc.request.domain.enums import RequestStatus
        assert saved.status == RequestStatus.SUBMITTED

    def test_repair_always_submitted(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="repair", title="Broken screen", description="Cracked",
                department_has_manager=True,
            )
        )

        saved = repo.save.call_args[0][0]
        from src.request_bc.request.domain.enums import RequestStatus
        assert saved.status == RequestStatus.SUBMITTED


class TestCreateRequestWorkflowTemplate:
    def test_workflow_template_id_passed_to_entity(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="incident", title="Test", description="Test description",
                workflow_template_id="tmpl_123",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.workflow_template_id == "tmpl_123"
        assert saved.workflow_subtype_id is None

    def test_workflow_template_and_subtype_ids_passed(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="new_equipment", title="Need laptop", description="For work",
                workflow_template_id="tmpl_456",
                workflow_subtype_id="sub_789",
                subtype="Computer",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.workflow_template_id == "tmpl_456"
        assert saved.workflow_subtype_id == "sub_789"
        assert saved.subtype == "Computer"

    def test_template_skips_subtype_enum_validation(self):
        """When workflow_template_id is provided, any subtype string is accepted."""
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="incident", title="Test", description="Test description",
                workflow_template_id="tmpl_123",
                subtype="CustomSubtype",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.subtype == "CustomSubtype"

    def test_without_template_fields_backward_compatible(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="incident", title="Test", description="Test description",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.workflow_template_id is None
        assert saved.workflow_subtype_id is None


class TestCreateRequestAIClassification:
    def test_ai_priority_hint_passed_to_scorer(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="incident", title="Test", description="Test description",
                ai_priority_hint=2,
            )
        )

        saved = repo.save.call_args[0][0]
        breakdown = saved.data["priority_scoring"]
        assert breakdown["ai_hint_weight"] == 2
        # incident(2) + ai_hint(2) = 4 → urgent
        assert saved.priority.value == "urgent"

    def test_ai_priority_hint_default_zero_unaffected(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="incident", title="Test", description="Test description",
            )
        )

        saved = repo.save.call_args[0][0]
        breakdown = saved.data["priority_scoring"]
        assert breakdown["ai_hint_weight"] == 0
        assert breakdown["raw_score"] == 2  # incident(2) only

    def test_ai_classification_merged_into_data(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        ai_meta = {"ai_used": True, "provider": "openai", "confidence": 0.9}
        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="incident", title="Test", description="Test description",
                ai_classification=ai_meta,
            )
        )

        saved = repo.save.call_args[0][0]
        assert "ai_classification" in saved.data
        assert saved.data["ai_classification"]["ai_used"] is True
        assert saved.data["ai_classification"]["provider"] == "openai"

    def test_ai_classification_none_no_key_in_data(self):
        repo = _make_repo()
        handler = CreateRequestCommandHandler(request_repo=repo)

        handler.handle(
            CreateRequestCommand(
                company_id="comp1", created_by="user1",
                type="incident", title="Test", description="Test description",
                ai_classification=None,
            )
        )

        saved = repo.save.call_args[0][0]
        assert "ai_classification" not in saved.data
