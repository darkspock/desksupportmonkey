from unittest.mock import MagicMock

import pytest

from src.sla_bc.sla.application.commands.create_policy import (
    CreateSlaPolicyCommand,
    CreateSlaPolicyCommandHandler,
)
from src.sla_bc.sla.domain.exceptions import (
    DuplicateSlaPolicyError,
    InvalidSlaTargetsError,
)


class TestCreateSlaPolicyCommand:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = CreateSlaPolicyCommandHandler(sla_repo=self.repo)

    def test_creates_policy(self):
        self.repo.find_active_policy_by_scope.return_value = None

        self.handler.handle(
            CreateSlaPolicyCommand(
                policy_id="p1",
                company_id="c1",
                name="Standard",
                priority="high",
                response_time_hours=4,
                resolution_time_hours=24,
            )
        )

        self.repo.save_policy.assert_called_once()
        saved = self.repo.save_policy.call_args[0][0]
        assert saved.name == "Standard"
        assert saved.priority == "high"
        assert saved.response_time_hours == 4
        assert saved.resolution_time_hours == 24

    def test_raises_duplicate(self):
        self.repo.find_active_policy_by_scope.return_value = MagicMock()

        with pytest.raises(DuplicateSlaPolicyError):
            self.handler.handle(
                CreateSlaPolicyCommand(
                    policy_id="p1",
                    company_id="c1",
                    name="Dup",
                    priority="high",
                    response_time_hours=4,
                    resolution_time_hours=24,
                )
            )

    def test_raises_invalid_targets(self):
        self.repo.find_active_policy_by_scope.return_value = None

        with pytest.raises(InvalidSlaTargetsError):
            self.handler.handle(
                CreateSlaPolicyCommand(
                    policy_id="p1",
                    company_id="c1",
                    name="Bad",
                    priority="high",
                    response_time_hours=24,
                    resolution_time_hours=24,
                )
            )
