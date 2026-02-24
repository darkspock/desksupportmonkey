import pytest

from src.sla_bc.sla.domain.entities import SlaBreachRecord, SlaPolicy
from src.sla_bc.sla.domain.enums import SlaBreachType
from src.sla_bc.sla.domain.exceptions import InvalidSlaTargetsError


class TestSlaPolicy:
    def test_create_valid(self):
        policy = SlaPolicy.create(
            company_id="c1",
            name="Standard SLA",
            priority="high",
            response_time_hours=4,
            resolution_time_hours=24,
        )
        assert policy.name == "Standard SLA"
        assert policy.priority == "high"
        assert policy.response_time_hours == 4
        assert policy.resolution_time_hours == 24
        assert policy.warning_threshold_pct == 75
        assert policy.escalate_on_breach is False
        assert policy.is_active is True
        assert policy.request_type is None
        assert policy.id is not None

    def test_create_with_request_type(self):
        policy = SlaPolicy.create(
            company_id="c1",
            name="VIP SLA",
            priority="urgent",
            response_time_hours=1,
            resolution_time_hours=4,
            request_type="incident",
        )
        assert policy.request_type == "incident"

    def test_create_with_custom_threshold(self):
        policy = SlaPolicy.create(
            company_id="c1",
            name="Test",
            priority="low",
            response_time_hours=24,
            resolution_time_hours=168,
            warning_threshold_pct=50,
            escalate_on_breach=True,
        )
        assert policy.warning_threshold_pct == 50
        assert policy.escalate_on_breach is True

    def test_create_invalid_response_gte_resolution(self):
        with pytest.raises(InvalidSlaTargetsError):
            SlaPolicy.create(
                company_id="c1",
                name="Bad",
                priority="high",
                response_time_hours=24,
                resolution_time_hours=24,
            )

    def test_create_invalid_response_gt_resolution(self):
        with pytest.raises(InvalidSlaTargetsError):
            SlaPolicy.create(
                company_id="c1",
                name="Bad",
                priority="high",
                response_time_hours=48,
                resolution_time_hours=24,
            )

    def test_create_invalid_zero_hours(self):
        with pytest.raises(InvalidSlaTargetsError):
            SlaPolicy.create(
                company_id="c1",
                name="Bad",
                priority="high",
                response_time_hours=0,
                resolution_time_hours=24,
            )

    def test_create_invalid_threshold(self):
        with pytest.raises(ValueError, match="Warning threshold"):
            SlaPolicy.create(
                company_id="c1",
                name="Bad",
                priority="high",
                response_time_hours=4,
                resolution_time_hours=24,
                warning_threshold_pct=0,
            )

    def test_create_strips_name(self):
        policy = SlaPolicy.create(
            company_id="c1",
            name="  Trimmed  ",
            priority="low",
            response_time_hours=24,
            resolution_time_hours=168,
        )
        assert policy.name == "Trimmed"

    def test_update(self):
        policy = SlaPolicy.create(
            company_id="c1",
            name="Original",
            priority="high",
            response_time_hours=4,
            resolution_time_hours=24,
        )
        old_updated = policy.updated_at
        policy.update(
            name="Updated",
            response_time_hours=2,
            resolution_time_hours=12,
            warning_threshold_pct=80,
            escalate_on_breach=True,
        )
        assert policy.name == "Updated"
        assert policy.response_time_hours == 2
        assert policy.resolution_time_hours == 12
        assert policy.warning_threshold_pct == 80
        assert policy.escalate_on_breach is True
        assert policy.updated_at >= old_updated

    def test_update_partial(self):
        policy = SlaPolicy.create(
            company_id="c1",
            name="Original",
            priority="high",
            response_time_hours=4,
            resolution_time_hours=24,
        )
        policy.update(name="Just Name")
        assert policy.name == "Just Name"
        assert policy.response_time_hours == 4

    def test_update_invalid_targets(self):
        policy = SlaPolicy.create(
            company_id="c1",
            name="Test",
            priority="high",
            response_time_hours=4,
            resolution_time_hours=24,
        )
        with pytest.raises(InvalidSlaTargetsError):
            policy.update(response_time_hours=30)

    def test_deactivate(self):
        policy = SlaPolicy.create(
            company_id="c1",
            name="Test",
            priority="high",
            response_time_hours=4,
            resolution_time_hours=24,
        )
        assert policy.is_active is True
        policy.deactivate()
        assert policy.is_active is False


class TestSlaBreachRecord:
    def test_create(self):
        breach = SlaBreachRecord.create(
            company_id="c1",
            request_id="r1",
            policy_id="p1",
            breach_type=SlaBreachType.RESPONSE_BREACH,
            target_hours=4.0,
            actual_hours=6.5,
        )
        assert breach.company_id == "c1"
        assert breach.request_id == "r1"
        assert breach.policy_id == "p1"
        assert breach.breach_type == SlaBreachType.RESPONSE_BREACH
        assert breach.target_hours == 4.0
        assert breach.actual_hours == 6.5
        assert breach.escalated is False
        assert breach.id is not None

    def test_create_with_escalation(self):
        breach = SlaBreachRecord.create(
            company_id="c1",
            request_id="r1",
            policy_id="p1",
            breach_type=SlaBreachType.RESOLUTION_BREACH,
            target_hours=24.0,
            actual_hours=30.0,
            escalated=True,
        )
        assert breach.escalated is True


class TestSlaBreachType:
    def test_count(self):
        assert len(SlaBreachType) == 4

    def test_values(self):
        assert SlaBreachType.RESPONSE_WARNING.value == "response_warning"
        assert SlaBreachType.RESPONSE_BREACH.value == "response_breach"
        assert SlaBreachType.RESOLUTION_WARNING.value == "resolution_warning"
        assert SlaBreachType.RESOLUTION_BREACH.value == "resolution_breach"
