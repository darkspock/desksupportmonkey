import logging
import os
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader

from core.celery import celery_app
from core.config import settings

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates"
)
_jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

REPORT_TYPE_LABELS = {
    "early_warning_24h": "Early Warning (24h)",
    "detailed_72h": "Detailed Report (72h)",
    "final_30d": "Final Report (30d)",
}


def _get_html_class():
    try:
        from weasyprint import HTML as WeasyHTML
    except (ImportError, OSError) as exc:
        raise RuntimeError(
            "Report generation unavailable: missing WeasyPrint system libraries."
        ) from exc
    return WeasyHTML


@celery_app.task(
    name="core.tasks.incidents.generate_incident_report",
    bind=True,
    max_retries=3,
)
def generate_incident_report(self, report_id: str, incident_id: str):
    """Generate a NIS2 regulatory report PDF."""
    from core.database import SessionLocal
    from core.storage import S3StorageService
    from src.incident_bc.incident.infrastructure.repository import IncidentRepository

    session = SessionLocal()
    try:
        repo = IncidentRepository(session)

        report = repo.find_report_by_id(report_id, incident_id)
        if not report:
            logger.error("Report not found: %s", report_id)
            return

        # Load incident (find without company_id filter for Celery context)
        from sqlalchemy import select
        from src.incident_bc.incident.infrastructure.models import SecurityIncidentModel

        model = session.execute(
            select(SecurityIncidentModel).where(
                SecurityIncidentModel.id == incident_id
            )
        ).scalar_one_or_none()
        if not model:
            logger.error("Incident not found: %s", incident_id)
            return
        incident = repo._to_entity(model)

        # Collect timeline
        timeline = repo.find_timeline(incident_id)

        # Resolve user names
        from src.auth_bc.user.infrastructure.repository import UserRepository

        user_repo = UserRepository(session)
        user_ids = {incident.reported_by}
        if incident.assigned_to:
            user_ids.add(incident.assigned_to)
        for entry in timeline:
            user_ids.add(entry.actor_id)
        users = user_repo.find_by_ids(list(user_ids))
        name_map: dict[str, str] = {}
        for uid, user in users.items():
            name_map[uid] = user.name.strip() if user.name and user.name.strip() else user.email

        # Get company name
        from src.company_bc.company.infrastructure.repository import CompanyRepository

        company_repo = CompanyRepository(session)
        company = company_repo.find_by_id(incident.company_id)
        company_name = company.name if company else "Unknown"

        # Build template data
        template_data = {
            "title": f"NIS2 Regulatory Report — {REPORT_TYPE_LABELS.get(report.report_type.value, report.report_type.value)}",
            "company_name": company_name,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "report_type": report.report_type.value,
            "report_type_label": REPORT_TYPE_LABELS.get(report.report_type.value, report.report_type.value),
            "incident_id": incident.id,
            "incident_title": incident.title,
            "description": incident.description,
            "severity": incident.severity.value,
            "status": incident.status.value.replace("_", " ").title(),
            "incident_type": incident.incident_type.value.replace("_", " ").title(),
            "detected_at": incident.detected_at.strftime("%Y-%m-%d %H:%M UTC") if incident.detected_at else "—",
            "deadline_at": report.deadline_at.strftime("%Y-%m-%d %H:%M UTC") if report.deadline_at else "—",
            "reported_by": name_map.get(incident.reported_by, incident.reported_by),
            "assigned_to": name_map.get(incident.assigned_to, incident.assigned_to) if incident.assigned_to else None,
            "attack_vector": incident.attack_vector,
            "data_breach_scope": incident.data_breach_scope,
            "close_reason": incident.close_reason,
            "closed_at": incident.closed_at.strftime("%Y-%m-%d %H:%M UTC") if incident.closed_at else None,
            "timeline": [
                {
                    "created_at": e.created_at.strftime("%Y-%m-%d %H:%M") if e.created_at else "—",
                    "event_type": e.event_type.value.replace("_", " ").title(),
                    "description": e.description,
                    "actor_id": e.actor_id,
                    "actor_name": name_map.get(e.actor_id),
                }
                for e in timeline
            ],
        }

        # Render HTML
        template = _jinja_env.get_template("reports/incident_report.html")
        html_content = template.render(**template_data)

        # Convert to PDF
        html_cls = _get_html_class()
        pdf_bytes = html_cls(string=html_content).write_pdf()

        # Upload to S3
        storage_key = f"incident-reports/{incident.company_id}/{incident_id}/{report_id}.pdf"
        storage = S3StorageService()
        storage.upload(storage_key, pdf_bytes)

        # Update report
        report.mark_generated(storage_key)
        repo.update_report(report)

        session.commit()
        logger.info(
            "Incident report %s generated: %s", report_id, storage_key
        )

    except Exception as exc:
        session.rollback()
        logger.exception("Incident report generation failed for %s", report_id)
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(name="core.tasks.incidents.check_regulatory_deadlines")
def check_regulatory_deadlines():
    """
    Runs every 15 minutes via Celery beat.
    Checks all pending/generated regulatory reports for approaching deadlines.
    Sends notifications at 75%, 90%, and 100% (overdue) thresholds.
    """
    from core.database import SessionLocal
    from src.incident_bc.incident.application.services.incident_event_factory import (
        IncidentEventFactory,
    )
    from src.incident_bc.incident.infrastructure.repository import IncidentRepository
    from src.notification_bc.notification.application.services.event_bus import EventBus
    from src.notification_bc.notification.application.services.notification_subscriber import (
        NotificationSubscriber,
    )
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )
    from src.auth_bc.user.infrastructure.repository import UserRepository

    session = SessionLocal()
    try:
        repo = IncidentRepository(session)
        reports_with_incidents = repo.find_pending_reports_approaching_deadline()

        now = datetime.now(timezone.utc)
        notifications_sent = 0

        for report, incident in reports_with_incidents:
            deadline = report.deadline_at
            detected = incident.detected_at

            total_duration = (deadline - detected).total_seconds()
            if total_duration <= 0:
                continue

            elapsed = (now - detected).total_seconds()
            elapsed_percentage = (elapsed / total_duration) * 100

            # Determine notification level based on elapsed percentage
            # Use timeline metadata to track sent notifications to avoid duplicates
            timeline_entries = repo.find_timeline(incident.id)
            sent_levels: set[str] = set()
            for entry in timeline_entries:
                if entry.metadata and entry.metadata.get("deadline_check"):
                    key = f"{report.id}_{entry.metadata.get('deadline_level', '')}"
                    sent_levels.add(key)

            event = None

            if elapsed_percentage >= 100:
                level_key = f"{report.id}_passed"
                if level_key not in sent_levels:
                    event = IncidentEventFactory.deadline_passed(
                        incident, report.report_type.value
                    )
                    # Log timeline entry
                    from src.incident_bc.incident.domain.entities import IncidentTimeline
                    from src.incident_bc.incident.domain.enums import TimelineEventType

                    tl = IncidentTimeline.create(
                        incident_id=incident.id,
                        event_type=TimelineEventType.ESCALATION,
                        description=f"NIS2 deadline PASSED for {report.report_type.value.replace('_', ' ')}",
                        actor_id="system",
                        metadata={
                            "report_id": report.id,
                            "deadline_check": True,
                            "deadline_level": "passed",
                        },
                    )
                    repo.save_timeline(tl)

            elif elapsed_percentage >= 90:
                level_key = f"{report.id}_urgent"
                if level_key not in sent_levels:
                    event = IncidentEventFactory.deadline_warning(
                        incident, report.report_type.value, 90
                    )
                    from src.incident_bc.incident.domain.entities import IncidentTimeline
                    from src.incident_bc.incident.domain.enums import TimelineEventType

                    tl = IncidentTimeline.create(
                        incident_id=incident.id,
                        event_type=TimelineEventType.ESCALATION,
                        description=f"NIS2 deadline urgent (90%): {report.report_type.value.replace('_', ' ')}",
                        actor_id="system",
                        metadata={
                            "report_id": report.id,
                            "deadline_check": True,
                            "deadline_level": "urgent",
                        },
                    )
                    repo.save_timeline(tl)

            elif elapsed_percentage >= 75:
                level_key = f"{report.id}_warning"
                if level_key not in sent_levels:
                    event = IncidentEventFactory.deadline_warning(
                        incident, report.report_type.value, 75
                    )
                    from src.incident_bc.incident.domain.entities import IncidentTimeline
                    from src.incident_bc.incident.domain.enums import TimelineEventType

                    tl = IncidentTimeline.create(
                        incident_id=incident.id,
                        event_type=TimelineEventType.ESCALATION,
                        description=f"NIS2 deadline warning (75%): {report.report_type.value.replace('_', ' ')}",
                        actor_id="system",
                        metadata={
                            "report_id": report.id,
                            "deadline_check": True,
                            "deadline_level": "warning",
                        },
                    )
                    repo.save_timeline(tl)

            if event:
                try:
                    user_repo = UserRepository(session)
                    notif_repo = NotificationRepository(session)
                    event_bus = EventBus()
                    subscriber = NotificationSubscriber(
                        user_repo=user_repo, notification_repo=notif_repo
                    )
                    event_bus.subscribe(subscriber)
                    event_bus.publish(event, session)
                    notifications_sent += 1
                except Exception:
                    logger.exception(
                        "Failed to send deadline notification for report %s",
                        report.id,
                    )

        session.commit()
        if notifications_sent:
            logger.info(
                "Deadline check completed: %d notifications sent",
                notifications_sent,
            )

    except Exception:
        session.rollback()
        logger.exception("Deadline check failed")
    finally:
        session.close()
