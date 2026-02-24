from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.audit_bc.audit.application.queries.list_compliance_controls import (
    ListComplianceControlsQuery,
    ListComplianceControlsQueryHandler,
)
from src.audit_bc.audit.domain.entities import ComplianceControl


class TestListComplianceControlsQueryHandler:
    def test_returns_controls(self):
        repo = MagicMock()
        repo.find_controls.return_value = [
            ComplianceControl(
                id="c1", company_id=None, code="NIS2-ART21-2A",
                name="Risk analysis", framework="NIS2", description=None,
                is_predefined=True, is_active=True,
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
            ComplianceControl(
                id="c2", company_id="comp1", code="CUSTOM-001",
                name="Custom Control", framework="CUSTOM", description="desc",
                is_predefined=False, is_active=True,
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            ),
        ]
        handler = ListComplianceControlsQueryHandler(repo=repo)

        result = handler.handle(
            ListComplianceControlsQuery(company_id="comp1")
        )

        assert len(result) == 2
        assert result[0].code == "NIS2-ART21-2A"
        assert result[0].is_predefined is True
        assert result[1].code == "CUSTOM-001"
        assert result[1].is_predefined is False

    def test_returns_empty_list(self):
        repo = MagicMock()
        repo.find_controls.return_value = []
        handler = ListComplianceControlsQueryHandler(repo=repo)

        result = handler.handle(
            ListComplianceControlsQuery(company_id="comp1")
        )

        assert result == []
