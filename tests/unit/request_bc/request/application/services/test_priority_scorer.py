from src.request_bc.request.application.services.priority_scorer import PriorityScorer
from src.request_bc.request.domain.enums import RequestPriority, RequestType


class TestPriorityScorer:
    def setup_method(self):
        self.scorer = PriorityScorer()

    def test_incident_security_high_dept_admin_urgent(self):
        # incident(2) + security(1) + dept(+2) + admin(1) = 6 → urgent
        priority, breakdown = self.scorer.compute(
            request_type=RequestType.INCIDENT,
            subtype="security",
            department_priority_weight=2,
            user_role="admin",
        )
        assert priority == RequestPriority.URGENT
        assert breakdown["raw_score"] == 6
        assert breakdown["type_weight"] == 2
        assert breakdown["subtype_weight"] == 1
        assert breakdown["department_weight"] == 2
        assert breakdown["role_weight"] == 1

    def test_incident_no_subtype_default_dept_employee_medium(self):
        # incident(2) + no subtype(0) + dept(0) + employee(0) = 2 → medium
        priority, breakdown = self.scorer.compute(
            request_type=RequestType.INCIDENT,
            subtype=None,
            department_priority_weight=0,
            user_role="employee",
        )
        assert priority == RequestPriority.MEDIUM
        assert breakdown["raw_score"] == 2

    def test_new_equipment_no_subtype_default_dept_employee_low(self):
        # new_equipment(0) + no subtype(0) + dept(0) + employee(0) = 0 → low
        priority, breakdown = self.scorer.compute(
            request_type=RequestType.NEW_EQUIPMENT,
            subtype=None,
            department_priority_weight=0,
            user_role="employee",
        )
        assert priority == RequestPriority.LOW
        assert breakdown["raw_score"] == 0

    def test_repair_hardware_dept_plus1_admin_urgent(self):
        # repair(1) + hardware(1) + dept(+1) + admin(1) = 4 → urgent
        priority, breakdown = self.scorer.compute(
            request_type=RequestType.REPAIR,
            subtype="hardware",
            department_priority_weight=1,
            user_role="admin",
        )
        assert priority == RequestPriority.URGENT
        assert breakdown["raw_score"] == 4

    def test_configuration_no_subtype_dept_minus1_employee_low(self):
        # configuration(0) + no subtype(0) + dept(-1) + employee(0) = -1 → low
        priority, breakdown = self.scorer.compute(
            request_type=RequestType.CONFIGURATION,
            subtype=None,
            department_priority_weight=-1,
            user_role="employee",
        )
        assert priority == RequestPriority.LOW
        assert breakdown["raw_score"] == -1

    def test_onboarding_no_subtype_default_dept_employee_low(self):
        # onboarding(1) + no subtype(0) + dept(0) + employee(0) = 1 → low
        priority, breakdown = self.scorer.compute(
            request_type=RequestType.ONBOARDING,
            subtype=None,
            department_priority_weight=0,
            user_role="employee",
        )
        assert priority == RequestPriority.LOW
        assert breakdown["raw_score"] == 1

    def test_score_boundary_exactly_2_medium(self):
        # incident(2) = 2 → medium
        priority, _ = self.scorer.compute(
            request_type=RequestType.INCIDENT,
            subtype=None,
            department_priority_weight=0,
            user_role="employee",
        )
        assert priority == RequestPriority.MEDIUM

    def test_score_boundary_exactly_3_high(self):
        # incident(2) + hardware(1) = 3 → high
        priority, _ = self.scorer.compute(
            request_type=RequestType.INCIDENT,
            subtype="hardware",
            department_priority_weight=0,
            user_role="employee",
        )
        assert priority == RequestPriority.HIGH

    def test_score_boundary_exactly_4_urgent(self):
        # incident(2) + hardware(1) + dept(1) = 4 → urgent
        priority, _ = self.scorer.compute(
            request_type=RequestType.INCIDENT,
            subtype="hardware",
            department_priority_weight=1,
            user_role="employee",
        )
        assert priority == RequestPriority.URGENT

    def test_score_boundary_exactly_1_low(self):
        # onboarding(1) = 1 → low
        priority, _ = self.scorer.compute(
            request_type=RequestType.ONBOARDING,
            subtype=None,
            department_priority_weight=0,
            user_role="employee",
        )
        assert priority == RequestPriority.LOW

    def test_unrecognized_subtype_no_weight(self):
        # subtype not in SUBTYPE_WEIGHTS → 0
        priority, breakdown = self.scorer.compute(
            request_type=RequestType.REPAIR,
            subtype="other",
            department_priority_weight=0,
            user_role="employee",
        )
        assert breakdown["subtype_weight"] == 0
        assert breakdown["raw_score"] == 1  # repair(1) only


class TestPriorityScorerAIHint:
    def setup_method(self):
        self.scorer = PriorityScorer()

    def test_ai_hint_zero_no_effect(self):
        # incident(2) + ai_hint(0) = 2 → medium
        priority, breakdown = self.scorer.compute(
            request_type=RequestType.INCIDENT,
            subtype=None,
            department_priority_weight=0,
            user_role="employee",
            ai_priority_hint=0,
        )
        assert breakdown["ai_hint_weight"] == 0
        assert breakdown["raw_score"] == 2
        assert priority == RequestPriority.MEDIUM

    def test_ai_hint_positive_adds_to_score(self):
        # incident(2) + ai_hint(2) = 4 → urgent
        priority, breakdown = self.scorer.compute(
            request_type=RequestType.INCIDENT,
            subtype=None,
            department_priority_weight=0,
            user_role="employee",
            ai_priority_hint=2,
        )
        assert breakdown["ai_hint_weight"] == 2
        assert breakdown["raw_score"] == 4
        assert priority == RequestPriority.URGENT

    def test_ai_hint_negative_subtracts_from_score(self):
        # incident(2) + ai_hint(-1) = 1 → low
        priority, breakdown = self.scorer.compute(
            request_type=RequestType.INCIDENT,
            subtype=None,
            department_priority_weight=0,
            user_role="employee",
            ai_priority_hint=-1,
        )
        assert breakdown["ai_hint_weight"] == -1
        assert breakdown["raw_score"] == 1
        assert priority == RequestPriority.LOW

    def test_ai_hint_pushes_medium_to_urgent(self):
        # incident(2) + hardware(1) + ai_hint(1) = 4 → urgent (was high at 3)
        priority_without, _ = self.scorer.compute(
            request_type=RequestType.INCIDENT,
            subtype="hardware",
            department_priority_weight=0,
            user_role="employee",
            ai_priority_hint=0,
        )
        assert priority_without == RequestPriority.HIGH

        priority_with, breakdown = self.scorer.compute(
            request_type=RequestType.INCIDENT,
            subtype="hardware",
            department_priority_weight=0,
            user_role="employee",
            ai_priority_hint=1,
        )
        assert priority_with == RequestPriority.URGENT
        assert breakdown["raw_score"] == 4

    def test_new_equipment_computer_urgent_hint_can_reach_urgent(self):
        # new_equipment(0) + computer(0) + ai_hint(2 boosted to 4) = 4 → urgent
        priority, breakdown = self.scorer.compute(
            request_type=RequestType.NEW_EQUIPMENT,
            subtype="computer",
            department_priority_weight=0,
            user_role="employee",
            ai_priority_hint=2,
        )
        assert breakdown["ai_hint_weight"] == 4
        assert breakdown["raw_score"] == 4
        assert priority == RequestPriority.URGENT

    def test_new_equipment_computer_without_ai_hint_stays_low(self):
        # new_equipment(0) + computer(0) + ai_hint(0) = 0 → low
        priority, breakdown = self.scorer.compute(
            request_type=RequestType.NEW_EQUIPMENT,
            subtype="computer",
            department_priority_weight=0,
            user_role="employee",
            ai_priority_hint=0,
        )
        assert breakdown["ai_hint_weight"] == 0
        assert breakdown["raw_score"] == 0
        assert priority == RequestPriority.LOW
