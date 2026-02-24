from unittest.mock import MagicMock, call

import pytest

from src.risk_bc.risk.application.commands.assess_risk import (
    AssessRiskCommand,
    AssessRiskCommandHandler,
)
from src.risk_bc.risk.application.commands.change_risk_status import (
    ChangeRiskStatusCommand,
    ChangeRiskStatusCommandHandler,
)
from src.risk_bc.risk.application.commands.create_risk import (
    CreateRiskCommand,
    CreateRiskCommandHandler,
)
from src.risk_bc.risk.application.commands.delete_risk import (
    DeleteRiskCommand,
    DeleteRiskCommandHandler,
)
from src.risk_bc.risk.application.commands.set_treatment import (
    SetTreatmentCommand,
    SetTreatmentCommandHandler,
)
from src.risk_bc.risk.application.commands.update_risk import (
    UpdateRiskCommand,
    UpdateRiskCommandHandler,
)
from src.risk_bc.risk.domain.entities import Risk
from src.risk_bc.risk.domain.enums import (
    RiskCategory,
    RiskLevel,
    RiskStatus,
    RiskTreatment,
)
from src.risk_bc.risk.domain.exceptions import (
    InvalidStatusTransitionError,
    RiskClosedError,
    RiskNotFoundError,
)


def _make_risk(**overrides):
    defaults = dict(
        id="r1",
        company_id="c1",
        title="Test Risk",
        description="Test description",
        category=RiskCategory.CYBER,
        status=RiskStatus.OPEN,
        created_by="u1",
    )
    defaults.update(overrides)
    return Risk(**defaults)


class TestCreateRiskCommandHandler:
    def test_creates_risk_and_history(self):
        repo = MagicMock()
        handler = CreateRiskCommandHandler(risk_repo=repo)
        handler.handle(
            CreateRiskCommand(
                risk_id="r1",
                company_id="c1",
                title="New Risk",
                description="Desc",
                category="cyber",
                created_by="u1",
            )
        )
        repo.save.assert_called_once()
        repo.add_history.assert_called_once()
        saved_risk = repo.save.call_args[0][0]
        assert saved_risk.title == "New Risk"
        assert saved_risk.status == RiskStatus.OPEN

    def test_invalid_category_raises(self):
        repo = MagicMock()
        handler = CreateRiskCommandHandler(risk_repo=repo)
        with pytest.raises(ValueError):
            handler.handle(
                CreateRiskCommand(
                    risk_id="r1",
                    company_id="c1",
                    title="Risk",
                    description="Desc",
                    category="invalid",
                    created_by="u1",
                )
            )


class TestAssessRiskCommandHandler:
    def test_assesses_risk(self):
        repo = MagicMock()
        risk = _make_risk()
        repo.find_by_id.return_value = risk

        handler = AssessRiskCommandHandler(risk_repo=repo)
        handler.handle(
            AssessRiskCommand(
                risk_id="r1",
                company_id="c1",
                actor_id="u1",
                likelihood=4,
                impact=5,
            )
        )
        repo.save.assert_called_once()
        assert risk.risk_level == RiskLevel.CRITICAL

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = AssessRiskCommandHandler(risk_repo=repo)
        with pytest.raises(RiskNotFoundError):
            handler.handle(
                AssessRiskCommand(
                    risk_id="r1",
                    company_id="c1",
                    actor_id="u1",
                    likelihood=3,
                    impact=3,
                )
            )

    def test_records_old_and_new_in_history(self):
        repo = MagicMock()
        risk = _make_risk(likelihood=2, impact=2, risk_level=RiskLevel.LOW)
        repo.find_by_id.return_value = risk

        handler = AssessRiskCommandHandler(risk_repo=repo)
        handler.handle(
            AssessRiskCommand(
                risk_id="r1",
                company_id="c1",
                actor_id="u1",
                likelihood=5,
                impact=5,
            )
        )
        history_entry = repo.add_history.call_args[0][0]
        assert history_entry.metadata["old_likelihood"] == 2
        assert history_entry.metadata["new_level"] == "critical"


class TestChangeRiskStatusCommandHandler:
    def test_changes_status(self):
        repo = MagicMock()
        risk = _make_risk()
        repo.find_by_id.return_value = risk

        handler = ChangeRiskStatusCommandHandler(risk_repo=repo)
        handler.handle(
            ChangeRiskStatusCommand(
                risk_id="r1",
                company_id="c1",
                actor_id="u1",
                new_status="under_review",
            )
        )
        assert risk.status == RiskStatus.UNDER_REVIEW
        repo.save.assert_called_once()

    def test_invalid_transition_raises(self):
        repo = MagicMock()
        risk = _make_risk()
        repo.find_by_id.return_value = risk

        handler = ChangeRiskStatusCommandHandler(risk_repo=repo)
        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                ChangeRiskStatusCommand(
                    risk_id="r1",
                    company_id="c1",
                    actor_id="u1",
                    new_status="mitigated",
                )
            )


class TestSetTreatmentCommandHandler:
    def test_sets_treatment(self):
        repo = MagicMock()
        risk = _make_risk()
        repo.find_by_id.return_value = risk

        handler = SetTreatmentCommandHandler(risk_repo=repo)
        handler.handle(
            SetTreatmentCommand(
                risk_id="r1",
                company_id="c1",
                actor_id="u1",
                treatment="mitigate",
            )
        )
        assert risk.treatment == RiskTreatment.MITIGATE
        repo.save.assert_called_once()


class TestUpdateRiskCommandHandler:
    def test_updates_risk(self):
        repo = MagicMock()
        risk = _make_risk()
        repo.find_by_id.return_value = risk

        handler = UpdateRiskCommandHandler(risk_repo=repo)
        handler.handle(
            UpdateRiskCommand(
                risk_id="r1",
                company_id="c1",
                actor_id="u1",
                title="Updated Title",
            )
        )
        assert risk.title == "Updated Title"
        repo.save.assert_called_once()

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = UpdateRiskCommandHandler(risk_repo=repo)
        with pytest.raises(RiskNotFoundError):
            handler.handle(
                UpdateRiskCommand(
                    risk_id="r1",
                    company_id="c1",
                    actor_id="u1",
                    title="X",
                )
            )


class TestDeleteRiskCommandHandler:
    def test_deletes_risk(self):
        repo = MagicMock()
        risk = _make_risk()
        repo.find_by_id.return_value = risk

        handler = DeleteRiskCommandHandler(risk_repo=repo)
        handler.handle(
            DeleteRiskCommand(risk_id="r1", company_id="c1")
        )
        repo.delete.assert_called_once_with("r1", "c1")

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = DeleteRiskCommandHandler(risk_repo=repo)
        with pytest.raises(RiskNotFoundError):
            handler.handle(
                DeleteRiskCommand(risk_id="r1", company_id="c1")
            )
