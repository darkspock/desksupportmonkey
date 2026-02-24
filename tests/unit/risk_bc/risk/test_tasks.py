from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.risk_bc.risk.domain.entities import Risk
from src.risk_bc.risk.domain.enums import RiskCategory, RiskStatus


def _make_overdue_risk(risk_id: str = "risk-1", owner_id: str | None = "user-1") -> Risk:
    return Risk(
        id=risk_id,
        company_id="company-1",
        title="Test risk",
        description="Description",
        category=RiskCategory.CYBER.value,
        status=RiskStatus.OPEN.value,
        created_by="creator-1",
        owner_id=owner_id,
        next_review_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


class TestCheckOverdueReviews:
    @patch("core.database.SessionLocal")
    def test_sends_notification_for_overdue_risk(self, mock_session_local: MagicMock):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.execute.return_value.scalars.return_value.all.return_value = [
            "company-1"
        ]

        risk = _make_overdue_risk()

        with (
            patch(
                "src.risk_bc.risk.infrastructure.repository.RiskRepository"
            ) as MockRiskRepo,
            patch(
                "src.notification_bc.notification.infrastructure.repository.NotificationRepository"
            ) as MockNotifRepo,
        ):
            mock_risk_repo = MockRiskRepo.return_value
            mock_notif_repo = MockNotifRepo.return_value
            mock_risk_repo.find_overdue_reviews.return_value = [risk]
            mock_risk_repo.get_history.return_value = []

            from core.tasks.risks import check_overdue_reviews

            result = check_overdue_reviews()

        assert result == 1
        mock_notif_repo.save.assert_called_once()
        mock_risk_repo.add_history.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("core.database.SessionLocal")
    def test_skips_already_alerted_risk(self, mock_session_local: MagicMock):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.execute.return_value.scalars.return_value.all.return_value = [
            "company-1"
        ]

        risk = _make_overdue_risk()

        existing_history = MagicMock()
        existing_history.event_type = "review_completed"
        existing_history.metadata = {
            "review_overdue_alert": True,
            "next_review_at": "2026-01-01T00:00:00+00:00",
        }

        with (
            patch(
                "src.risk_bc.risk.infrastructure.repository.RiskRepository"
            ) as MockRiskRepo,
            patch(
                "src.notification_bc.notification.infrastructure.repository.NotificationRepository"
            ),
        ):
            mock_risk_repo = MockRiskRepo.return_value
            mock_risk_repo.find_overdue_reviews.return_value = [risk]
            mock_risk_repo.get_history.return_value = [existing_history]

            from core.tasks.risks import check_overdue_reviews

            result = check_overdue_reviews()

        assert result == 0

    @patch("core.database.SessionLocal")
    def test_no_overdue_returns_zero(self, mock_session_local: MagicMock):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.execute.return_value.scalars.return_value.all.return_value = [
            "company-1"
        ]

        with (
            patch(
                "src.risk_bc.risk.infrastructure.repository.RiskRepository"
            ) as MockRiskRepo,
            patch(
                "src.notification_bc.notification.infrastructure.repository.NotificationRepository"
            ),
        ):
            mock_risk_repo = MockRiskRepo.return_value
            mock_risk_repo.find_overdue_reviews.return_value = []

            from core.tasks.risks import check_overdue_reviews

            result = check_overdue_reviews()

        assert result == 0
