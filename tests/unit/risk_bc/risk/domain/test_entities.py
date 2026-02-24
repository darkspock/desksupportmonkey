import pytest

from src.risk_bc.risk.domain.entities import MitigationPlan, Risk, RiskHistory, RiskLink
from src.risk_bc.risk.domain.enums import (
    MitigationStatus,
    RiskCategory,
    RiskHistoryEventType,
    RiskLevel,
    RiskLinkType,
    RiskStatus,
    RiskTreatment,
    calculate_risk_level,
)
from src.risk_bc.risk.domain.exceptions import (
    InvalidStatusTransitionError,
    RiskClosedError,
)


class TestRiskCreate:
    def test_creates_with_open_status(self):
        risk = Risk.create(
            company_id="c1",
            title="Data leak risk",
            description="Sensitive data may be exposed",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        assert risk.title == "Data leak risk"
        assert risk.status == RiskStatus.OPEN
        assert risk.category == RiskCategory.CYBER
        assert risk.likelihood is None
        assert risk.impact is None
        assert risk.risk_level is None
        assert risk.id is not None

    def test_strips_whitespace(self):
        risk = Risk.create(
            company_id="c1",
            title="  Title  ",
            description="  Desc  ",
            category=RiskCategory.OPERATIONAL,
            created_by="u1",
        )
        assert risk.title == "Title"
        assert risk.description == "Desc"

    def test_empty_title_raises(self):
        with pytest.raises(ValueError, match="Title is required"):
            Risk.create(
                company_id="c1",
                title="",
                description="Desc",
                category=RiskCategory.CYBER,
                created_by="u1",
            )

    def test_empty_description_raises(self):
        with pytest.raises(ValueError, match="Description is required"):
            Risk.create(
                company_id="c1",
                title="Title",
                description="   ",
                category=RiskCategory.CYBER,
                created_by="u1",
            )

    def test_sets_owner_id(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.COMPLIANCE,
            created_by="u1",
            owner_id="u2",
        )
        assert risk.owner_id == "u2"


class TestRiskAssess:
    def test_calculates_risk_level(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        risk.assess(4, 5)
        assert risk.likelihood == 4
        assert risk.impact == 5
        assert risk.risk_level == RiskLevel.CRITICAL

    def test_low_scores_give_low_level(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        risk.assess(1, 1)
        assert risk.risk_level == RiskLevel.LOW

    def test_medium_scores(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        risk.assess(3, 3)
        assert risk.risk_level == RiskLevel.MEDIUM

    def test_invalid_likelihood_raises(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        with pytest.raises(ValueError, match="Likelihood must be between"):
            risk.assess(0, 3)

    def test_invalid_impact_raises(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        with pytest.raises(ValueError, match="Impact must be between"):
            risk.assess(3, 6)

    def test_closed_risk_cannot_assess(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        risk.status = RiskStatus.CLOSED
        with pytest.raises(RiskClosedError):
            risk.assess(3, 3)


class TestRiskStatusTransitions:
    def test_open_to_under_review(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        risk.change_status(RiskStatus.UNDER_REVIEW)
        assert risk.status == RiskStatus.UNDER_REVIEW

    def test_open_to_accepted(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        risk.change_status(RiskStatus.ACCEPTED)
        assert risk.status == RiskStatus.ACCEPTED

    def test_open_to_mitigated_invalid(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        with pytest.raises(InvalidStatusTransitionError):
            risk.change_status(RiskStatus.MITIGATED)

    def test_closed_to_open(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        risk.change_status(RiskStatus.CLOSED)
        risk.change_status(RiskStatus.OPEN)
        assert risk.status == RiskStatus.OPEN

    def test_under_review_to_mitigated(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        risk.change_status(RiskStatus.UNDER_REVIEW)
        risk.change_status(RiskStatus.MITIGATED)
        assert risk.status == RiskStatus.MITIGATED


class TestRiskTreatment:
    def test_set_treatment(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        risk.set_treatment(RiskTreatment.MITIGATE)
        assert risk.treatment == RiskTreatment.MITIGATE

    def test_closed_risk_cannot_set_treatment(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        risk.status = RiskStatus.CLOSED
        with pytest.raises(RiskClosedError):
            risk.set_treatment(RiskTreatment.ACCEPT)


class TestRiskUpdateDetails:
    def test_updates_fields(self):
        risk = Risk.create(
            company_id="c1",
            title="Old",
            description="Old desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        risk.update_details(
            title="New Title",
            category=RiskCategory.OPERATIONAL,
        )
        assert risk.title == "New Title"
        assert risk.category == RiskCategory.OPERATIONAL

    def test_closed_risk_cannot_update(self):
        risk = Risk.create(
            company_id="c1",
            title="Risk",
            description="Desc",
            category=RiskCategory.CYBER,
            created_by="u1",
        )
        risk.status = RiskStatus.CLOSED
        with pytest.raises(RiskClosedError):
            risk.update_details(title="New")


class TestRiskLevelMatrix:
    @pytest.mark.parametrize(
        "likelihood,impact,expected",
        [
            (1, 1, RiskLevel.LOW),
            (1, 5, RiskLevel.MEDIUM),
            (2, 5, RiskLevel.HIGH),
            (4, 5, RiskLevel.CRITICAL),
            (5, 5, RiskLevel.CRITICAL),
            (5, 1, RiskLevel.MEDIUM),
            (3, 3, RiskLevel.MEDIUM),
            (4, 3, RiskLevel.HIGH),
        ],
    )
    def test_matrix(self, likelihood, impact, expected):
        assert calculate_risk_level(likelihood, impact) == expected


class TestMitigationPlan:
    def test_create(self):
        plan = MitigationPlan.create(
            risk_id="r1",
            description="Install firewall",
            owner_id="u1",
        )
        assert plan.status == MitigationStatus.OPEN
        assert plan.description == "Install firewall"

    def test_empty_description_raises(self):
        with pytest.raises(ValueError, match="Mitigation description"):
            MitigationPlan.create(risk_id="r1", description="")

    def test_update_status(self):
        plan = MitigationPlan.create(risk_id="r1", description="Do thing")
        plan.update_status(MitigationStatus.IN_PROGRESS)
        assert plan.status == MitigationStatus.IN_PROGRESS
