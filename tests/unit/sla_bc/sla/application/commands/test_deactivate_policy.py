from unittest.mock import MagicMock

import pytest

from src.sla_bc.sla.application.commands.deactivate_policy import (
    DeactivateSlaPolicyCommand,
    DeactivateSlaPolicyCommandHandler,
)
from src.sla_bc.sla.domain.entities import SlaPolicy
from src.sla_bc.sla.domain.exceptions import SlaPolicyNotFoundError


class TestDeactivateSlaPolicyCommand:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = DeactivateSlaPolicyCommandHandler(sla_repo=self.repo)

    def test_deactivates_policy(self):
        policy = SlaPolicy.create(
            company_id="c1",
            name="Test",
            priority="high",
            response_time_hours=4,
            resolution_time_hours=24,
        )
        self.repo.find_policy_by_id.return_value = policy

        self.handler.handle(
            DeactivateSlaPolicyCommand(policy_id="p1", company_id="c1")
        )

        self.repo.save_policy.assert_called_once()
        saved = self.repo.save_policy.call_args[0][0]
        assert saved.is_active is False

    def test_raises_not_found(self):
        self.repo.find_policy_by_id.return_value = None

        with pytest.raises(SlaPolicyNotFoundError):
            self.handler.handle(
                DeactivateSlaPolicyCommand(policy_id="nope", company_id="c1")
            )
