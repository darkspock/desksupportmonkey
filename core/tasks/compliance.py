import logging
import os
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from core.celery import celery_app

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "templates",
)
_jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


@celery_app.task(
    name="core.tasks.compliance.generate_compliance_report",
    bind=True,
    max_retries=3,
)
def generate_compliance_report(
    self,
    company_id: str,
    requested_by: str,
    framework: Optional[str] = None,
):
    """Generate compliance posture PDF report and upload to MinIO."""
    from datetime import datetime, timezone

    from core.database import SessionLocal
    from core.storage import S3StorageService
    from core.tasks.reports import _get_html_class
    from src.audit_bc.audit.application.queries \
            .get_compliance_dashboard import (
        GetComplianceDashboardQuery,
        GetComplianceDashboardQueryHandler,
    )
    from src.audit_bc.audit.infrastructure.repository import (
        AuditRepository,
    )
    from src.notification_bc.notification.domain.entities import (
        Notification,
    )
    from src.notification_bc.notification.domain.enums import EventType
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )

    session = SessionLocal()
    try:
        repo = AuditRepository(session)
        handler = GetComplianceDashboardQueryHandler(repo=repo)
        dashboard = handler.handle(
            GetComplianceDashboardQuery(
                company_id=company_id,
                framework=framework,
            )
        )

        task_id = self.request.id or "unknown"
        generated_at = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        )

        template = _jinja_env.get_template(
            "reports/compliance_report.html"
        )
        html_content = template.render(
            title="Compliance Posture Report",
            company_id=company_id,
            generated_at=generated_at,
            framework_filter=framework,
            overall_compliance_pct=dashboard.overall_compliance_pct,
            total_controls=dashboard.total_controls,
            compliant=dashboard.compliant,
            partial=dashboard.partial,
            non_compliant=dashboard.non_compliant,
            not_assessed=dashboard.not_assessed,
            controls_with_evidence=dashboard.controls_with_evidence,
            controls_without_evidence=dashboard.controls_without_evidence,
            frameworks=[f.__dict__ for f in dashboard.frameworks],
            gap_controls=[g.__dict__ for g in dashboard.gap_controls],
        )

        html_cls = _get_html_class()
        pdf_bytes: bytes = html_cls(string=html_content).write_pdf()

        storage_key = (
            f"compliance-reports/{company_id}/{task_id}.pdf"
        )
        storage = S3StorageService()
        storage.upload(storage_key, pdf_bytes)

        notif = Notification.create(
            user_id=requested_by,
            company_id=company_id,
            event_type=EventType.COMPLIANCE_REPORT_READY.value,
            title="Compliance report ready",
            body="Your compliance posture report is ready for download",
            data={"storage_key": storage_key},
        )
        NotificationRepository(session).save(notif)

        session.commit()
        logger.info(
            "Compliance report generated for company %s: %s",
            company_id,
            storage_key,
        )

    except Exception as exc:
        session.rollback()
        logger.exception(
            "Compliance report failed for company %s", company_id
        )
        raise self.retry(exc=exc)
    finally:
        session.close()
