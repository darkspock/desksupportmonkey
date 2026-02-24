from unittest.mock import MagicMock

import pytest

from src.risk_bc.risk.application.queries.get_risk_detail import (
    GetRiskDetailQuery,
    GetRiskDetailQueryHandler,
)
from src.risk_bc.risk.application.queries.list_risks import (
    ListRisksQuery,
    ListRisksQueryHandler,
)
from src.risk_bc.risk.domain.entities import (
    MitigationPlan,
    Risk,
    RiskHistory,
    RiskLink,
)
from src.risk_bc.risk.domain.enums import (
    MitigationStatus,
    RiskCategory,
    RiskHistoryEventType,
    RiskLevel,
    RiskLinkType,
    RiskStatus,
)
from src.risk_bc.risk.domain.exceptions import RiskNotFoundError


def _make_risk(**overrides):
    defaults = dict(
        id="r1",
        company_id="c1",
        title="Test Risk",
        description="Test description",
        category=RiskCategory.CYBER,
        status=RiskStatus.OPEN,
        created_by="u1",
        likelihood=3,
        impact=4,
        risk_level=RiskLevel.HIGH,
    )
    defaults.update(overrides)
    return Risk(**defaults)


class TestListRisksQueryHandler:
    def test_returns_risks_with_total(self):
        repo = MagicMock()
        risk = _make_risk()
        repo.find_all.return_value = ([risk], 1)

        handler = ListRisksQueryHandler(risk_repo=repo)
        dtos, total = handler.handle(
            ListRisksQuery(company_id="c1")
        )
        assert total == 1
        assert len(dtos) == 1
        assert dtos[0].id == "r1"
        assert dtos[0].risk_level == "high"

    def test_empty_list(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)

        handler = ListRisksQueryHandler(risk_repo=repo)
        dtos, total = handler.handle(
            ListRisksQuery(company_id="c1")
        )
        assert total == 0
        assert dtos == []

    def test_resolves_owner_names(self):
        repo = MagicMock()
        risk = _make_risk(owner_id="u2")
        repo.find_all.return_value = ([risk], 1)

        resolver = MagicMock(return_value={"u2": "John Doe"})
        handler = ListRisksQueryHandler(
            risk_repo=repo, user_name_resolver=resolver
        )
        dtos, _ = handler.handle(ListRisksQuery(company_id="c1"))
        assert dtos[0].owner_name == "John Doe"


class TestGetRiskDetailQueryHandler:
    def test_returns_full_detail(self):
        repo = MagicMock()
        risk = _make_risk(owner_id="u2")
        repo.find_by_id.return_value = risk
        repo.get_mitigations.return_value = [
            MitigationPlan(
                id="m1",
                risk_id="r1",
                description="Fix it",
                status=MitigationStatus.OPEN,
                owner_id="u3",
            )
        ]
        repo.get_links.return_value = [
            RiskLink(
                id="l1",
                risk_id="r1",
                link_type=RiskLinkType.ASSET,
                link_id="a1",
            )
        ]
        repo.get_history.return_value = [
            RiskHistory(
                id="h1",
                risk_id="r1",
                event_type=RiskHistoryEventType.CREATED,
                description="Risk created",
                actor_id="u1",
            )
        ]

        resolver = MagicMock(
            return_value={"u1": "Admin", "u2": "Owner", "u3": "Tech"}
        )
        handler = GetRiskDetailQueryHandler(
            risk_repo=repo, user_name_resolver=resolver
        )
        dto = handler.handle(
            GetRiskDetailQuery(risk_id="r1", company_id="c1")
        )
        assert dto.id == "r1"
        assert dto.owner_name == "Owner"
        assert dto.created_by_name == "Admin"
        assert len(dto.mitigations) == 1
        assert dto.mitigations[0].owner_name == "Tech"
        assert len(dto.links) == 1
        assert dto.links[0].link_type == "asset"
        assert len(dto.history) == 1

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetRiskDetailQueryHandler(risk_repo=repo)
        with pytest.raises(RiskNotFoundError):
            handler.handle(
                GetRiskDetailQuery(risk_id="r1", company_id="c1")
            )

    def test_without_name_resolver(self):
        repo = MagicMock()
        risk = _make_risk()
        repo.find_by_id.return_value = risk
        repo.get_mitigations.return_value = []
        repo.get_links.return_value = []
        repo.get_history.return_value = []

        handler = GetRiskDetailQueryHandler(risk_repo=repo)
        dto = handler.handle(
            GetRiskDetailQuery(risk_id="r1", company_id="c1")
        )
        assert dto.owner_name is None
        assert dto.created_by_name is None
