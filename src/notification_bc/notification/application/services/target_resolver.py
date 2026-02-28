from src.notification_bc.notification.application.ports import UserLookup
from src.notification_bc.notification.domain.enums import EventType
from src.notification_bc.notification.domain.events import DomainEvent


class TargetResolver:
    def __init__(self, user_repo: UserLookup):
        self.user_repo = user_repo

    def resolve(self, event: DomainEvent) -> list[str]:
        resolvers = {
            EventType.REQUEST_CREATED: self._resolve_request_created,
            EventType.REQUEST_STATUS_CHANGED: self._resolve_request_status_changed,
            EventType.REQUEST_ASSIGNED: self._resolve_request_assigned,
            EventType.REQUEST_PRIORITY_CHANGED: self._resolve_request_priority_changed,
            EventType.REQUEST_COMMENT_ADDED: self._resolve_request_comment_added,
            EventType.REQUEST_NOTE_ADDED: self._resolve_request_note_added,
            EventType.REQUEST_APPROVAL_NEEDED: self._resolve_approval_needed,
            EventType.REQUEST_APPROVED: self._resolve_request_approved,
            EventType.REPORT_READY: self._resolve_report_ready,
            EventType.PO_SUBMITTED: self._resolve_po_submitted,
            EventType.PO_APPROVED: self._resolve_po_approved,
            EventType.PO_CANCELLED: self._resolve_po_cancelled,
            EventType.BUDGET_THRESHOLD_REACHED: self._resolve_budget_threshold,
            EventType.PO_RECEIVED: self._resolve_po_received,
            EventType.APPOINTMENT_CREATED: self._resolve_appointment_created,
            EventType.APPOINTMENT_CONFIRMED: self._resolve_appointment_confirmed,
            EventType.APPOINTMENT_CANCELLED: self._resolve_appointment_cancelled,
            EventType.APPOINTMENT_RESCHEDULED: self._resolve_appointment_rescheduled,
            EventType.APPOINTMENT_COMPLETED: self._resolve_appointment_completed,
            EventType.SHIPMENT_CREATED: self._resolve_shipment_created,
            EventType.SHIPMENT_DISPATCHED: self._resolve_shipment_dispatched,
            EventType.SHIPMENT_DELIVERED: self._resolve_shipment_delivered,
            EventType.SHIPMENT_FAILED: self._resolve_shipment_failed,
            EventType.SHIPMENT_CANCELLED: self._resolve_shipment_cancelled,
            EventType.MAINTENANCE_SCHEDULED: self._resolve_maintenance_scheduled,
            EventType.MAINTENANCE_DUE: self._resolve_maintenance_due,
            EventType.MAINTENANCE_OVERDUE: self._resolve_maintenance_overdue,
            EventType.MAINTENANCE_COMPLETED: self._resolve_maintenance_completed,
            EventType.MAINTENANCE_CANCELLED: self._resolve_maintenance_cancelled,
            EventType.INCIDENT_CREATED: self._resolve_incident_created,
            EventType.INCIDENT_STATUS_CHANGED: self._resolve_incident_status_changed,
            EventType.INCIDENT_SEVERITY_CHANGED: self._resolve_incident_severity_changed,
            EventType.INCIDENT_ASSIGNED: self._resolve_incident_assigned,
            EventType.INCIDENT_EMPLOYEE_REPORTED: self._resolve_incident_employee_reported,
            EventType.INCIDENT_DEADLINE_WARNING: self._resolve_incident_deadline_warning,
            EventType.INCIDENT_DEADLINE_URGENT: self._resolve_incident_deadline_admins,
            EventType.INCIDENT_DEADLINE_PASSED: self._resolve_incident_deadline_admins,
            EventType.RISK_REVIEW_OVERDUE: self._resolve_risk_review_overdue,
            EventType.SLA_WARNING: self._resolve_sla_warning,
            EventType.SLA_RESPONSE_BREACHED: self._resolve_sla_breach,
            EventType.SLA_RESOLUTION_BREACHED: self._resolve_sla_breach,
            EventType.VULNERABILITY_CRITICAL_REGISTERED: self._resolve_vuln_critical,
            EventType.VULNERABILITY_REMEDIATION_OVERDUE: self._resolve_vuln_critical,
            EventType.CHANGE_APPROVED: self._resolve_change_requester,
            EventType.CHANGE_REJECTED: self._resolve_change_requester,
        }
        resolver = resolvers.get(event.event_type)  # type: ignore[call-overload]
        if resolver is None:
            return []
        targets = resolver(event)
        targets.discard(event.actor_id)
        return list(targets)

    def _resolve_request_created(self, event: DomainEvent) -> set[str]:
        tech_ids = self.user_repo.find_technician_ids_by_company(event.company_id)
        return set(tech_ids)

    def _resolve_request_status_changed(self, event: DomainEvent) -> set[str]:
        targets = set()
        created_by = event.payload.get("created_by")
        assigned_to = event.payload.get("assigned_to")
        if created_by:
            targets.add(created_by)
        if assigned_to:
            targets.add(assigned_to)
        return targets

    def _resolve_request_assigned(self, event: DomainEvent) -> set[str]:
        targets = set()
        assigned_to = event.payload.get("assigned_to")
        if assigned_to:
            targets.add(assigned_to)
        return targets

    def _resolve_request_priority_changed(self, event: DomainEvent) -> set[str]:
        targets = set()
        assigned_to = event.payload.get("assigned_to")
        if assigned_to:
            targets.add(assigned_to)
        return targets

    def _resolve_request_comment_added(self, event: DomainEvent) -> set[str]:
        targets = set()
        created_by = event.payload.get("created_by")
        assigned_to = event.payload.get("assigned_to")
        if created_by:
            targets.add(created_by)
        if assigned_to:
            targets.add(assigned_to)
        return targets

    def _resolve_request_note_added(self, event: DomainEvent) -> set[str]:
        targets = set()
        assigned_to = event.payload.get("assigned_to")
        if assigned_to:
            targets.add(assigned_to)
        return targets

    def _resolve_approval_needed(self, event: DomainEvent) -> set[str]:
        manager_id = event.payload.get("department_manager_id")
        return {manager_id} if manager_id else set()

    def _resolve_request_approved(self, event: DomainEvent) -> set[str]:
        created_by = event.payload.get("created_by")
        return {created_by} if created_by else set()

    def _resolve_report_ready(self, event: DomainEvent) -> set[str]:
        requested_by = event.payload.get("requested_by")
        return {requested_by} if requested_by else set()

    def _resolve_po_submitted(self, event: DomainEvent) -> set[str]:
        admin_ids = self.user_repo.find_admin_ids_by_company(
            event.company_id,
        )
        return set(admin_ids)

    def _resolve_po_approved(self, event: DomainEvent) -> set[str]:
        created_by = event.payload.get("created_by")
        return {created_by} if created_by else set()

    def _resolve_po_cancelled(self, event: DomainEvent) -> set[str]:
        created_by = event.payload.get("created_by")
        return {created_by} if created_by else set()

    def _resolve_po_received(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        created_by = event.payload.get("created_by")
        if created_by:
            targets.add(created_by)
        admin_ids = self.user_repo.find_admin_ids_by_company(
            event.company_id,
        )
        targets.update(admin_ids)
        return targets

    def _resolve_budget_threshold(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        admin_ids = self.user_repo.find_admin_ids_by_company(
            event.company_id,
        )
        targets.update(admin_ids)
        manager_id = event.payload.get("department_manager_id")
        if manager_id:
            targets.add(manager_id)
        return targets

    def _resolve_appointment_created(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        technician_id = event.payload.get("technician_id")
        employee_id = event.payload.get("employee_id")
        if technician_id:
            targets.add(technician_id)
        if employee_id:
            targets.add(employee_id)
        return targets

    def _resolve_appointment_confirmed(self, event: DomainEvent) -> set[str]:
        employee_id = event.payload.get("employee_id")
        return {employee_id} if employee_id else set()

    def _resolve_appointment_cancelled(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        technician_id = event.payload.get("technician_id")
        employee_id = event.payload.get("employee_id")
        if technician_id:
            targets.add(technician_id)
        if employee_id:
            targets.add(employee_id)
        return targets

    def _resolve_appointment_rescheduled(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        technician_id = event.payload.get("technician_id")
        employee_id = event.payload.get("employee_id")
        if technician_id:
            targets.add(technician_id)
        if employee_id:
            targets.add(employee_id)
        return targets

    def _resolve_appointment_completed(self, event: DomainEvent) -> set[str]:
        employee_id = event.payload.get("employee_id")
        return {employee_id} if employee_id else set()

    def _resolve_shipment_created(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        recipient_user_id = event.payload.get("recipient_user_id")
        if recipient_user_id:
            targets.add(recipient_user_id)
        return targets

    def _resolve_shipment_dispatched(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        recipient_user_id = event.payload.get("recipient_user_id")
        if recipient_user_id:
            targets.add(recipient_user_id)
        return targets

    def _resolve_shipment_delivered(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        direction = event.payload.get("direction")
        if direction == "OUTBOUND":
            recipient_user_id = event.payload.get("recipient_user_id")
            if recipient_user_id:
                targets.add(recipient_user_id)
        else:
            created_by = event.payload.get("created_by")
            if created_by:
                targets.add(created_by)
        return targets

    def _resolve_shipment_failed(self, event: DomainEvent) -> set[str]:
        created_by = event.payload.get("created_by")
        return {created_by} if created_by else set()

    def _resolve_shipment_cancelled(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        recipient_user_id = event.payload.get("recipient_user_id")
        if recipient_user_id:
            targets.add(recipient_user_id)
        return targets

    def _resolve_maintenance_scheduled(self, event: DomainEvent) -> set[str]:
        technician_id = event.payload.get("technician_id")
        return {technician_id} if technician_id else set()

    def _resolve_maintenance_due(self, event: DomainEvent) -> set[str]:
        technician_id = event.payload.get("technician_id")
        return {technician_id} if technician_id else set()

    def _resolve_maintenance_overdue(self, event: DomainEvent) -> set[str]:
        technician_id = event.payload.get("technician_id")
        return {technician_id} if technician_id else set()

    def _resolve_maintenance_completed(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        technician_id = event.payload.get("technician_id")
        created_by = event.payload.get("created_by")
        if technician_id:
            targets.add(technician_id)
        if created_by:
            targets.add(created_by)
        return targets

    def _resolve_maintenance_cancelled(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        technician_id = event.payload.get("technician_id")
        created_by = event.payload.get("created_by")
        if technician_id:
            targets.add(technician_id)
        if created_by:
            targets.add(created_by)
        return targets

    # --- Incident events ---

    def _resolve_incident_created(self, event: DomainEvent) -> set[str]:
        tech_ids = self.user_repo.find_technician_ids_by_company(event.company_id)
        return set(tech_ids)

    def _resolve_incident_status_changed(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        assigned_to = event.payload.get("assigned_to")
        if assigned_to:
            targets.add(assigned_to)
        admin_ids = self.user_repo.find_admin_ids_by_company(event.company_id)
        targets.update(admin_ids)
        return targets

    def _resolve_incident_severity_changed(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        assigned_to = event.payload.get("assigned_to")
        if assigned_to:
            targets.add(assigned_to)
        admin_ids = self.user_repo.find_admin_ids_by_company(event.company_id)
        targets.update(admin_ids)
        return targets

    def _resolve_incident_assigned(self, event: DomainEvent) -> set[str]:
        assigned_to = event.payload.get("assigned_to")
        return {assigned_to} if assigned_to else set()

    def _resolve_incident_employee_reported(self, event: DomainEvent) -> set[str]:
        tech_ids = self.user_repo.find_technician_ids_by_company(event.company_id)
        return set(tech_ids)

    def _resolve_incident_deadline_warning(self, event: DomainEvent) -> set[str]:
        admin_ids = self.user_repo.find_admin_ids_by_company(event.company_id)
        targets = set(admin_ids)
        assigned_to = event.payload.get("assigned_to") if event.payload else None
        if assigned_to:
            targets.add(assigned_to)
        return targets

    def _resolve_incident_deadline_admins(self, event: DomainEvent) -> set[str]:
        admin_ids = self.user_repo.find_admin_ids_by_company(event.company_id)
        return set(admin_ids)

    # --- Risk events ---

    def _resolve_risk_review_overdue(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        owner_id = event.payload.get("owner_id") if event.payload else None
        if owner_id:
            targets.add(owner_id)
        admin_ids = self.user_repo.find_admin_ids_by_company(event.company_id)
        targets.update(admin_ids)
        return targets

    # --- SLA events ---

    def _resolve_sla_warning(self, event: DomainEvent) -> set[str]:
        assigned_to = event.payload.get("assigned_to") if event.payload else None
        return {assigned_to} if assigned_to else set()

    def _resolve_sla_breach(self, event: DomainEvent) -> set[str]:
        targets: set[str] = set()
        assigned_to = event.payload.get("assigned_to") if event.payload else None
        if assigned_to:
            targets.add(assigned_to)
        admin_ids = self.user_repo.find_admin_ids_by_company(event.company_id)
        targets.update(admin_ids)
        return targets

    # --- Vulnerability events ---

    def _resolve_vuln_critical(self, event: DomainEvent) -> set[str]:
        admin_ids = self.user_repo.find_admin_ids_by_company(event.company_id)
        return set(admin_ids)

    # --- Change events ---

    def _resolve_change_requester(self, event: DomainEvent) -> set[str]:
        requested_by = event.payload.get("requested_by") if event.payload else None
        return {requested_by} if requested_by else set()
