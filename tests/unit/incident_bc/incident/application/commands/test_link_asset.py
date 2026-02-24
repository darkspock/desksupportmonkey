from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from src.incident_bc.incident.application.commands.link_asset import (
    LinkAssetCommand,
    LinkAssetCommandHandler,
)
from src.incident_bc.incident.application.commands.unlink_asset import (
    UnlinkAssetCommand,
    UnlinkAssetCommandHandler,
)
from src.incident_bc.incident.domain.enums import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
from src.incident_bc.incident.domain.entities import SecurityIncident
from src.incident_bc.incident.domain.exceptions import (
    AssetAlreadyLinkedError,
    IncidentClosedError,
    IncidentNotFoundError,
)

from datetime import datetime, timezone

NOW = datetime(2026, 2, 20, 10, 0, 0, tzinfo=timezone.utc)


def _make_incident(status: IncidentStatus = IncidentStatus.DETECTED) -> SecurityIncident:
    inc = SecurityIncident.create(
        company_id="comp1",
        title="Test Incident",
        description="Test description",
        incident_type=IncidentType.PHISHING,
        severity=IncidentSeverity.P2,
        detected_at=NOW,
        reported_by="user1",
        id="inc1",
    )
    inc.status = status
    return inc


class TestLinkAssetCommandHandler:
    def test_links_asset_and_creates_timeline(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()
        repo.save_incident_asset.return_value = "link1"

        handler = LinkAssetCommandHandler(incident_repo=repo)
        handler.handle(
            LinkAssetCommand(
                incident_id="inc1",
                company_id="comp1",
                asset_id="asset1",
                actor_id="user1",
                impact_description="Server compromised",
            )
        )

        repo.save_incident_asset.assert_called_once_with(
            incident_id="inc1",
            asset_id="asset1",
            impact_description="Server compromised",
        )
        repo.save_timeline.assert_called_once()
        timeline = repo.save_timeline.call_args[0][0]
        assert timeline.event_type.value == "asset_linked"

    def test_raises_when_incident_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = LinkAssetCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                LinkAssetCommand(
                    incident_id="inc1",
                    company_id="comp1",
                    asset_id="asset1",
                    actor_id="user1",
                )
            )

    def test_raises_when_incident_closed(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident(IncidentStatus.CLOSED)

        handler = LinkAssetCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentClosedError):
            handler.handle(
                LinkAssetCommand(
                    incident_id="inc1",
                    company_id="comp1",
                    asset_id="asset1",
                    actor_id="user1",
                )
            )

    def test_raises_on_duplicate_link(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()
        repo.save_incident_asset.side_effect = IntegrityError(
            "duplicate", params=None, orig=Exception()
        )

        handler = LinkAssetCommandHandler(incident_repo=repo)
        with pytest.raises(AssetAlreadyLinkedError):
            handler.handle(
                LinkAssetCommand(
                    incident_id="inc1",
                    company_id="comp1",
                    asset_id="asset1",
                    actor_id="user1",
                )
            )


class TestUnlinkAssetCommandHandler:
    def test_unlinks_asset_and_creates_timeline(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()

        handler = UnlinkAssetCommandHandler(incident_repo=repo)
        handler.handle(
            UnlinkAssetCommand(
                incident_id="inc1",
                company_id="comp1",
                asset_id="asset1",
                actor_id="user1",
            )
        )

        repo.delete_incident_asset.assert_called_once_with(
            incident_id="inc1",
            asset_id="asset1",
        )
        repo.save_timeline.assert_called_once()
        timeline = repo.save_timeline.call_args[0][0]
        assert timeline.event_type.value == "asset_unlinked"

    def test_raises_when_incident_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = UnlinkAssetCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                UnlinkAssetCommand(
                    incident_id="inc1",
                    company_id="comp1",
                    asset_id="asset1",
                    actor_id="user1",
                )
            )

    def test_raises_when_incident_closed(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident(IncidentStatus.CLOSED)

        handler = UnlinkAssetCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentClosedError):
            handler.handle(
                UnlinkAssetCommand(
                    incident_id="inc1",
                    company_id="comp1",
                    asset_id="asset1",
                    actor_id="user1",
                )
            )
