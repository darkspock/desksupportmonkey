from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from src.incident_bc.incident.application.commands.link_vendor import (
    LinkVendorCommand,
    LinkVendorCommandHandler,
)
from src.incident_bc.incident.application.commands.unlink_vendor import (
    UnlinkVendorCommand,
    UnlinkVendorCommandHandler,
)
from src.incident_bc.incident.domain.enums import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
from src.incident_bc.incident.domain.entities import SecurityIncident
from src.incident_bc.incident.domain.exceptions import (
    IncidentClosedError,
    IncidentNotFoundError,
    VendorAlreadyLinkedError,
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


class TestLinkVendorCommandHandler:
    def test_links_vendor_and_creates_timeline(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()
        repo.save_incident_vendor.return_value = "link1"

        handler = LinkVendorCommandHandler(incident_repo=repo)
        handler.handle(
            LinkVendorCommand(
                incident_id="inc1",
                company_id="comp1",
                vendor_id="vendor1",
                actor_id="user1",
                involvement_description="Third-party hosting",
            )
        )

        repo.save_incident_vendor.assert_called_once_with(
            incident_id="inc1",
            vendor_id="vendor1",
            involvement_description="Third-party hosting",
        )
        repo.save_timeline.assert_called_once()
        timeline = repo.save_timeline.call_args[0][0]
        assert timeline.event_type.value == "vendor_linked"

    def test_raises_when_incident_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = LinkVendorCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                LinkVendorCommand(
                    incident_id="inc1",
                    company_id="comp1",
                    vendor_id="vendor1",
                    actor_id="user1",
                )
            )

    def test_raises_when_incident_closed(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident(IncidentStatus.CLOSED)

        handler = LinkVendorCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentClosedError):
            handler.handle(
                LinkVendorCommand(
                    incident_id="inc1",
                    company_id="comp1",
                    vendor_id="vendor1",
                    actor_id="user1",
                )
            )

    def test_raises_on_duplicate_link(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()
        repo.save_incident_vendor.side_effect = IntegrityError(
            "duplicate", params=None, orig=Exception()
        )

        handler = LinkVendorCommandHandler(incident_repo=repo)
        with pytest.raises(VendorAlreadyLinkedError):
            handler.handle(
                LinkVendorCommand(
                    incident_id="inc1",
                    company_id="comp1",
                    vendor_id="vendor1",
                    actor_id="user1",
                )
            )


class TestUnlinkVendorCommandHandler:
    def test_unlinks_vendor_and_creates_timeline(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()

        handler = UnlinkVendorCommandHandler(incident_repo=repo)
        handler.handle(
            UnlinkVendorCommand(
                incident_id="inc1",
                company_id="comp1",
                vendor_id="vendor1",
                actor_id="user1",
            )
        )

        repo.delete_incident_vendor.assert_called_once_with(
            incident_id="inc1",
            vendor_id="vendor1",
        )
        repo.save_timeline.assert_called_once()
        timeline = repo.save_timeline.call_args[0][0]
        assert timeline.event_type.value == "vendor_unlinked"

    def test_raises_when_incident_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = UnlinkVendorCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                UnlinkVendorCommand(
                    incident_id="inc1",
                    company_id="comp1",
                    vendor_id="vendor1",
                    actor_id="user1",
                )
            )

    def test_raises_when_incident_closed(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident(IncidentStatus.CLOSED)

        handler = UnlinkVendorCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentClosedError):
            handler.handle(
                UnlinkVendorCommand(
                    incident_id="inc1",
                    company_id="comp1",
                    vendor_id="vendor1",
                    actor_id="user1",
                )
            )
