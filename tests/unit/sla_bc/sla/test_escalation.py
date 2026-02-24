from unittest.mock import MagicMock

from core.tasks.sla import PRIORITY_ESCALATION, _escalate_priority


class TestPriorityEscalation:
    def test_escalation_map_has_correct_entries(self):
        assert PRIORITY_ESCALATION == {
            "low": "medium",
            "medium": "high",
            "high": "urgent",
        }

    def test_escalates_low_to_medium(self):
        session = MagicMock()
        _escalate_priority(session, "req1", "low")
        session.execute.assert_called_once()
        params = session.execute.call_args[0][1]
        assert params == {"new_prio": "medium", "rid": "req1"}

    def test_escalates_medium_to_high(self):
        session = MagicMock()
        _escalate_priority(session, "req1", "medium")
        params = session.execute.call_args[0][1]
        assert params == {"new_prio": "high", "rid": "req1"}

    def test_escalates_high_to_urgent(self):
        session = MagicMock()
        _escalate_priority(session, "req1", "high")
        params = session.execute.call_args[0][1]
        assert params == {"new_prio": "urgent", "rid": "req1"}

    def test_does_not_escalate_urgent(self):
        session = MagicMock()
        _escalate_priority(session, "req1", "urgent")
        session.execute.assert_not_called()

    def test_does_not_escalate_unknown_priority(self):
        session = MagicMock()
        _escalate_priority(session, "req1", "critical")
        session.execute.assert_not_called()
