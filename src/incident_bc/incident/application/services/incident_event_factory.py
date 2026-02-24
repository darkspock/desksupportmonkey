from datetime import datetime, timezone

from src.incident_bc.incident.domain.entities import SecurityIncident
from src.notification_bc.notification.domain.events import DomainEvent


class IncidentEventFactory:
    @staticmethod
    def incident_created(
        incident: SecurityIncident, actor_id: str
    ) -> DomainEvent:
        return DomainEvent(
            event_type="incident.created",
            company_id=incident.company_id,
            actor_id=actor_id,
            payload={
                "incident_id": incident.id,
                "title": incident.title,
                "incident_type": incident.incident_type.value,
                "severity": incident.severity.value,
            },
            title=f"New security incident: {incident.severity.value}",
            body=incident.title,
        )

    @staticmethod
    def status_changed(
        incident: SecurityIncident,
        old_status: str,
        new_status: str,
        actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type="incident.status_changed",
            company_id=incident.company_id,
            actor_id=actor_id,
            payload={
                "incident_id": incident.id,
                "title": incident.title,
                "old_status": old_status,
                "new_status": new_status,
            },
            title=f"Incident status: {new_status}",
            body=f"{incident.title} — {old_status} → {new_status}",
        )

    @staticmethod
    def severity_changed(
        incident: SecurityIncident,
        old_severity: str,
        new_severity: str,
        actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type="incident.severity_changed",
            company_id=incident.company_id,
            actor_id=actor_id,
            payload={
                "incident_id": incident.id,
                "title": incident.title,
                "old_severity": old_severity,
                "new_severity": new_severity,
            },
            title=f"Incident severity: {new_severity}",
            body=f"{incident.title} — {old_severity} → {new_severity}",
        )

    @staticmethod
    def incident_assigned(
        incident: SecurityIncident,
        assigned_to: str,
        actor_id: str,
    ) -> DomainEvent:
        return DomainEvent(
            event_type="incident.assigned",
            company_id=incident.company_id,
            actor_id=actor_id,
            payload={
                "incident_id": incident.id,
                "title": incident.title,
                "assigned_to": assigned_to,
            },
            title="Incident assigned to you",
            body=incident.title,
        )

    @staticmethod
    def employee_reported(
        incident: SecurityIncident, actor_id: str
    ) -> DomainEvent:
        return DomainEvent(
            event_type="incident.employee_reported",
            company_id=incident.company_id,
            actor_id=actor_id,
            payload={
                "incident_id": incident.id,
                "title": incident.title,
                "incident_type": incident.incident_type.value,
            },
            title="Employee reported security incident",
            body=incident.title,
        )

    @staticmethod
    def deadline_warning(
        incident: SecurityIncident, report_type: str, percentage: int
    ) -> DomainEvent:
        event_type = (
            "incident.deadline_urgent"
            if percentage >= 90
            else "incident.deadline_warning"
        )
        label = report_type.replace("_", " ")
        return DomainEvent(
            event_type=event_type,
            company_id=incident.company_id,
            actor_id="system",
            payload={
                "incident_id": incident.id,
                "title": incident.title,
                "report_type": report_type,
                "elapsed_percentage": percentage,
            },
            title=f"NIS2 deadline {'urgent' if percentage >= 90 else 'warning'}: {label}",
            body=f"{incident.title} — {percentage}% of deadline elapsed for {label}",
        )

    @staticmethod
    def deadline_passed(
        incident: SecurityIncident, report_type: str
    ) -> DomainEvent:
        label = report_type.replace("_", " ")
        return DomainEvent(
            event_type="incident.deadline_passed",
            company_id=incident.company_id,
            actor_id="system",
            payload={
                "incident_id": incident.id,
                "title": incident.title,
                "report_type": report_type,
            },
            title=f"NIS2 deadline PASSED: {label}",
            body=f"{incident.title} — deadline for {label} has passed without submission",
        )
