from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from src.request_bc.request.infrastructure.repository import RequestRepository


def _make_repo():
    session = MagicMock()
    repo = RequestRepository(session)
    return repo, session


class TestCountByStatus:
    def test_returns_all_statuses_with_defaults(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            ("submitted", 5),
            ("in_progress", 3),
        ]
        result = repo.count_by_status("comp1")
        assert result["submitted"] == 5
        assert result["in_progress"] == 3
        assert result["in_review"] == 0
        assert result["resolved"] == 0
        assert result["rejected"] == 0

    def test_empty_returns_all_zeros(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo.count_by_status("comp1")
        assert all(v == 0 for v in result.values())
        assert len(result) == 5


class TestCountByType:
    def test_returns_all_types_with_defaults(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            ("incident", 10),
        ]
        result = repo.count_by_type("comp1")
        assert result["incident"] == 10
        assert result["new_equipment"] == 0
        assert result["onboarding"] == 0


class TestCountByPriority:
    def test_returns_all_priorities_with_defaults(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            ("high", 7),
            ("urgent", 2),
        ]
        result = repo.count_by_priority("comp1")
        assert result["high"] == 7
        assert result["urgent"] == 2
        assert result["low"] == 0
        assert result["medium"] == 0


class TestAvgResolutionTime:
    def test_returns_float_hours(self):
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = 24.567
        result = repo.avg_resolution_time("comp1")
        assert result == 24.57

    def test_returns_none_when_no_resolved(self):
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = None
        result = repo.avg_resolution_time("comp1")
        assert result is None

    def test_with_date_filter(self):
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = 12.0
        result = repo.avg_resolution_time(
            "comp1",
            from_date=date(2026, 1, 1),
            to_date=date(2026, 1, 31),
        )
        assert result == 12.0
        session.execute.assert_called_once()


class TestAvgResolutionTimeByTechnician:
    def test_groups_correctly(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            ("tech1", 10.5, 5),
            ("tech2", 20.3, 3),
        ]
        result = repo.avg_resolution_time_by_technician("comp1")
        assert len(result) == 2
        assert result[0]["technician_id"] == "tech1"
        assert result[0]["avg_hours"] == 10.5
        assert result[0]["resolved_count"] == 5
        assert result[1]["technician_id"] == "tech2"

    def test_empty_returns_empty_list(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo.avg_resolution_time_by_technician("comp1")
        assert result == []


class TestCountByPeriod:
    def test_returns_bucketed_data(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            (datetime(2026, 1, 1, tzinfo=timezone.utc), "incident", 3),
            (datetime(2026, 1, 1, tzinfo=timezone.utc), "onboarding", 1),
            (datetime(2026, 1, 2, tzinfo=timezone.utc), "incident", 2),
        ]
        result = repo.count_by_period("comp1", "day", date(2026, 1, 1), date(2026, 1, 7))
        assert len(result) == 3
        assert result[0]["type"] == "incident"
        assert result[0]["count"] == 3

    def test_empty_returns_empty(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo.count_by_period("comp1", "day", date(2026, 1, 1), date(2026, 1, 7))
        assert result == []


class TestFindOpenRequestsWithAge:
    def test_returns_open_requests(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            ("req1", "Broken laptop", "incident", "high", "submitted", "tech1", datetime(2026, 1, 1, tzinfo=timezone.utc), 48.5),
        ]
        result = repo.find_open_requests_with_age("comp1")
        assert len(result) == 1
        assert result[0]["id"] == "req1"
        assert result[0]["hours_open"] == 48.5
        assert result[0]["priority"] == "high"

    def test_empty_returns_empty(self):
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo.find_open_requests_with_age("comp1")
        assert result == []
