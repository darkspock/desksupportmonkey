from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.change_bc.change_request.application.queries.change_dashboard import (
    ChangeDashboardQuery,
    ChangeDashboardQueryHandler,
)
from src.change_bc.change_request.domain.entities import ChangeRequest
from src.change_bc.change_request.domain.enums import (
    ChangeStatus,
    ChangeType,
)


COMPANY_ID = "01COMPANY00000000000000001"
USER_ID = "01USER00000000000000000001"


def _make_change(**overrides) -> ChangeRequest:
    defaults = dict(
        id="01CHANGE000000000000000001",
        company_id=COMPANY_ID,
        requested_by=USER_ID,
        title="Install security patch",
    )
    defaults.update(overrides)
    return ChangeRequest.create(**defaults)


def _make_dashboard_data(**overrides) -> dict:
    defaults = dict(
        status_counts={s.value: 0 for s in ChangeStatus},
        type_counts={t.value: 0 for t in ChangeType},
        upcoming_scheduled=[],
        recently_implemented=[],
        rolled_back_90_days=0,
        scheduled_this_week=0,
    )
    defaults.update(overrides)
    return defaults


class TestChangeDashboardQuery:
    def test_happy_path_empty_data(self):
        repo = MagicMock()
        repo.get_dashboard_data.return_value = _make_dashboard_data()
        handler = ChangeDashboardQueryHandler(change_repo=repo)

        dto = handler.handle(
            ChangeDashboardQuery(company_id=COMPANY_ID)
        )

        assert dto.total_open == 0
        assert dto.pending_approval == 0
        assert dto.in_progress == 0
        assert dto.implemented == 0
        assert dto.scheduled_this_week == 0
        assert dto.rolled_back_90_days == 0
        assert dto.upcoming_scheduled == []
        assert dto.recently_implemented == []
        assert len(dto.status_counts) == 8
        assert len(dto.type_counts) == 3

    def test_total_open_excludes_terminal(self):
        status_counts = {s.value: 0 for s in ChangeStatus}
        status_counts["draft"] = 2
        status_counts["pending_approval"] = 3
        status_counts["scheduled"] = 1
        status_counts["in_progress"] = 1
        status_counts["implemented"] = 2
        status_counts["closed"] = 10
        status_counts["rejected"] = 5
        status_counts["rolled_back"] = 3

        repo = MagicMock()
        repo.get_dashboard_data.return_value = _make_dashboard_data(
            status_counts=status_counts
        )
        handler = ChangeDashboardQueryHandler(change_repo=repo)

        dto = handler.handle(
            ChangeDashboardQuery(company_id=COMPANY_ID)
        )

        # 2+3+1+1+2 = 9 (excludes closed=10, rejected=5, rolled_back=3)
        assert dto.total_open == 9
        assert dto.pending_approval == 3
        assert dto.in_progress == 1
        assert dto.implemented == 2

    def test_upcoming_scheduled(self):
        change = _make_change()
        change.status = ChangeStatus.SCHEDULED
        change.planned_date = datetime(2026, 3, 5, 10, 0, tzinfo=timezone.utc)
        change.assigned_to = USER_ID

        repo = MagicMock()
        repo.get_dashboard_data.return_value = _make_dashboard_data(
            upcoming_scheduled=[change]
        )
        handler = ChangeDashboardQueryHandler(change_repo=repo)

        dto = handler.handle(
            ChangeDashboardQuery(company_id=COMPANY_ID)
        )

        assert len(dto.upcoming_scheduled) == 1
        assert dto.upcoming_scheduled[0].title == "Install security patch"
        assert dto.upcoming_scheduled[0].assigned_to == USER_ID

    def test_user_name_resolution(self):
        change = _make_change()
        change.status = ChangeStatus.SCHEDULED
        change.assigned_to = USER_ID

        repo = MagicMock()
        repo.get_dashboard_data.return_value = _make_dashboard_data(
            upcoming_scheduled=[change]
        )
        resolver = MagicMock(return_value={USER_ID: "John Doe"})
        handler = ChangeDashboardQueryHandler(
            change_repo=repo, user_name_resolver=resolver
        )

        dto = handler.handle(
            ChangeDashboardQuery(company_id=COMPANY_ID)
        )

        resolver.assert_called_once()
        assert dto.upcoming_scheduled[0].assigned_to_name == "John Doe"

    def test_recently_implemented(self):
        repo = MagicMock()
        repo.get_dashboard_data.return_value = _make_dashboard_data(
            recently_implemented=[
                {
                    "id": "01CHANGE001",
                    "title": "Deploy patch",
                    "change_type": "standard",
                    "implemented_at": datetime(
                        2026, 2, 25, 10, 0, tzinfo=timezone.utc
                    ),
                    "pir_outcome": "successful",
                },
                {
                    "id": "01CHANGE002",
                    "title": "Config update",
                    "change_type": "emergency",
                    "implemented_at": datetime(
                        2026, 2, 24, 10, 0, tzinfo=timezone.utc
                    ),
                    "pir_outcome": None,
                },
            ]
        )
        handler = ChangeDashboardQueryHandler(change_repo=repo)

        dto = handler.handle(
            ChangeDashboardQuery(company_id=COMPANY_ID)
        )

        assert len(dto.recently_implemented) == 2
        assert dto.recently_implemented[0].pir_outcome == "successful"
        assert dto.recently_implemented[1].pir_outcome is None

    def test_rolled_back_count(self):
        repo = MagicMock()
        repo.get_dashboard_data.return_value = _make_dashboard_data(
            rolled_back_90_days=4
        )
        handler = ChangeDashboardQueryHandler(change_repo=repo)

        dto = handler.handle(
            ChangeDashboardQuery(company_id=COMPANY_ID)
        )

        assert dto.rolled_back_90_days == 4

    def test_scheduled_this_week(self):
        repo = MagicMock()
        repo.get_dashboard_data.return_value = _make_dashboard_data(
            scheduled_this_week=3
        )
        handler = ChangeDashboardQueryHandler(change_repo=repo)

        dto = handler.handle(
            ChangeDashboardQuery(company_id=COMPANY_ID)
        )

        assert dto.scheduled_this_week == 3
