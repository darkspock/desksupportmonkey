from unittest.mock import MagicMock

from src.sla_bc.sla.application.commands.record_breach import (
    RecordSlaBreachCommand,
    RecordSlaBreachCommandHandler,
)


class TestRecordSlaBreachCommand:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = RecordSlaBreachCommandHandler(sla_repo=self.repo)

    def test_records_new_breach(self):
        self.repo.has_breach_of_type.return_value = False

        self.handler.handle(
            RecordSlaBreachCommand(
                company_id="c1",
                request_id="r1",
                policy_id="p1",
                breach_type="response_breach",
                target_hours=4.0,
                actual_hours=5.5,
            )
        )

        self.repo.save_breach.assert_called_once()
        saved = self.repo.save_breach.call_args[0][0]
        assert saved.request_id == "r1"
        assert saved.policy_id == "p1"
        assert saved.breach_type.value == "response_breach"
        assert saved.target_hours == 4.0
        assert saved.actual_hours == 5.5
        assert saved.escalated is False

    def test_skips_duplicate_breach(self):
        self.repo.has_breach_of_type.return_value = True

        self.handler.handle(
            RecordSlaBreachCommand(
                company_id="c1",
                request_id="r1",
                policy_id="p1",
                breach_type="response_breach",
                target_hours=4.0,
                actual_hours=5.5,
            )
        )

        self.repo.save_breach.assert_not_called()

    def test_records_with_escalation(self):
        self.repo.has_breach_of_type.return_value = False

        self.handler.handle(
            RecordSlaBreachCommand(
                company_id="c1",
                request_id="r1",
                policy_id="p1",
                breach_type="resolution_breach",
                target_hours=24.0,
                actual_hours=30.0,
                escalated=True,
            )
        )

        saved = self.repo.save_breach.call_args[0][0]
        assert saved.escalated is True
