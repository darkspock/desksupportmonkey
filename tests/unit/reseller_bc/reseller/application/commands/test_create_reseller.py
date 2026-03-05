from unittest.mock import MagicMock

import pytest

from src.reseller_bc.reseller.application.commands.create_reseller import (
    CreateResellerCommand,
    CreateResellerCommandHandler,
)
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerAlreadyExistsException,
    ReferralCodeCollisionException,
)


class TestCreateResellerCommandHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = CreateResellerCommandHandler(repo=self.repo)

    def test_create_success(self):
        self.repo.exists_by_email.return_value = False
        self.repo.exists_by_referral_code.return_value = False

        self.handler.handle(CreateResellerCommand(
            id="test-id",
            email="partner@example.com",
            name="Partner Inc",
            commission_pct=20,
            min_payout_cents=5000,
        ))

        self.repo.save.assert_called_once()
        saved_reseller = self.repo.save.call_args[0][0]
        assert saved_reseller.email == "partner@example.com"
        assert saved_reseller.name == "Partner Inc"
        assert saved_reseller.commission_pct == 20

    def test_create_duplicate_email(self):
        self.repo.exists_by_email.return_value = True

        with pytest.raises(ResellerAlreadyExistsException):
            self.handler.handle(CreateResellerCommand(
                id="test-id",
                email="existing@example.com",
                name="Test",
                commission_pct=20,
                min_payout_cents=5000,
            ))

        self.repo.save.assert_not_called()

    def test_create_referral_code_collision_retries(self):
        self.repo.exists_by_email.return_value = False
        # First 2 codes collide, third doesn't
        self.repo.exists_by_referral_code.side_effect = [True, True, False]

        self.handler.handle(CreateResellerCommand(
            id="test-id",
            email="partner@example.com",
            name="Partner Inc",
            commission_pct=20,
            min_payout_cents=5000,
        ))

        self.repo.save.assert_called_once()
        assert self.repo.exists_by_referral_code.call_count == 3

    def test_create_referral_code_all_collisions(self):
        self.repo.exists_by_email.return_value = False
        self.repo.exists_by_referral_code.return_value = True  # Always collides

        with pytest.raises(ReferralCodeCollisionException):
            self.handler.handle(CreateResellerCommand(
                id="test-id",
                email="partner@example.com",
                name="Partner Inc",
                commission_pct=20,
                min_payout_cents=5000,
            ))
