from datetime import datetime
from unittest.mock import MagicMock

from src.sla_bc.sla.application.queries.get_dashboard import (
    GetSlaDashboardQuery,
    GetSlaDashboardQueryHandler,
    SlaDashboardDto,
)


class TestGetSlaDashboardQuery:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = GetSlaDashboardQueryHandler(sla_repo=self.repo)
        self.from_date = datetime(2026, 1, 1)
        self.to_date = datetime(2026, 2, 1)

    def _query(self, bucket="week"):
        return GetSlaDashboardQuery(
            company_id="c1",
            from_date=self.from_date,
            to_date=self.to_date,
            bucket=bucket,
        )

    def test_returns_overall_stats(self):
        self.repo.compliance_stats.return_value = {
            "total_resolved": 100,
            "met": 85,
            "breached": 15,
            "compliance_pct": 85.0,
        }
        self.repo.compliance_by_priority.return_value = []
        self.repo.compliance_by_type.return_value = []
        self.repo.breach_trend.return_value = []

        dto = self.handler.handle(self._query())

        assert isinstance(dto, SlaDashboardDto)
        assert dto.total_resolved == 100
        assert dto.met == 85
        assert dto.breached == 15
        assert dto.compliance_pct == 85.0

    def test_returns_by_priority(self):
        self.repo.compliance_stats.return_value = {
            "total_resolved": 50,
            "met": 40,
            "breached": 10,
            "compliance_pct": 80.0,
        }
        self.repo.compliance_by_priority.return_value = [
            {"priority": "urgent", "total": 10, "met": 7, "breached": 3, "compliance_pct": 70.0},
            {"priority": "high", "total": 20, "met": 18, "breached": 2, "compliance_pct": 90.0},
        ]
        self.repo.compliance_by_type.return_value = []
        self.repo.breach_trend.return_value = []

        dto = self.handler.handle(self._query())

        assert len(dto.by_priority) == 2
        assert dto.by_priority[0].group == "urgent"
        assert dto.by_priority[0].compliance_pct == 70.0
        assert dto.by_priority[1].group == "high"

    def test_returns_by_type(self):
        self.repo.compliance_stats.return_value = {
            "total_resolved": 30,
            "met": 25,
            "breached": 5,
            "compliance_pct": 83.3,
        }
        self.repo.compliance_by_priority.return_value = []
        self.repo.compliance_by_type.return_value = [
            {"type": "incident", "total": 15, "met": 12, "breached": 3, "compliance_pct": 80.0},
        ]
        self.repo.breach_trend.return_value = []

        dto = self.handler.handle(self._query())

        assert len(dto.by_type) == 1
        assert dto.by_type[0].group == "incident"
        assert dto.by_type[0].breached == 3

    def test_returns_breach_trend(self):
        self.repo.compliance_stats.return_value = {
            "total_resolved": 0,
            "met": 0,
            "breached": 0,
            "compliance_pct": 0.0,
        }
        self.repo.compliance_by_priority.return_value = []
        self.repo.compliance_by_type.return_value = []
        self.repo.breach_trend.return_value = [
            {"period": "2026-01-06", "count": 3},
            {"period": "2026-01-13", "count": 1},
        ]

        dto = self.handler.handle(self._query())

        assert len(dto.breach_trend) == 2
        assert dto.breach_trend[0].period == "2026-01-06"
        assert dto.breach_trend[0].count == 3

    def test_passes_bucket_to_repo(self):
        self.repo.compliance_stats.return_value = {
            "total_resolved": 0, "met": 0, "breached": 0, "compliance_pct": 0.0,
        }
        self.repo.compliance_by_priority.return_value = []
        self.repo.compliance_by_type.return_value = []
        self.repo.breach_trend.return_value = []

        self.handler.handle(self._query(bucket="month"))

        self.repo.breach_trend.assert_called_once_with(
            "c1", self.from_date, self.to_date, "month"
        )

    def test_empty_stats_returns_zeros(self):
        self.repo.compliance_stats.return_value = {}
        self.repo.compliance_by_priority.return_value = []
        self.repo.compliance_by_type.return_value = []
        self.repo.breach_trend.return_value = []

        dto = self.handler.handle(self._query())

        assert dto.total_resolved == 0
        assert dto.met == 0
        assert dto.breached == 0
        assert dto.compliance_pct == 0.0
