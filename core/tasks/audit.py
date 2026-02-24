import csv
import io
import logging
import os

from jinja2 import Environment, FileSystemLoader

from core.celery import celery_app

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates"
)
_jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

from core.config import settings  # noqa: E402
_jinja_env.globals["brand_name"] = settings.BRAND_NAME


@celery_app.task(
    name="core.tasks.audit.export_audit_log",
    bind=True,
    max_retries=3,
)
def export_audit_log(
    self,
    company_id: str,
    requested_by: str,
    export_format: str,
    filters: dict,
):
    """Export audit log as CSV or PDF and upload to MinIO."""
    from core.database import SessionLocal
    from core.storage import S3StorageService
    from src.audit_bc.audit.infrastructure.repository import AuditRepository
    from src.notification_bc.notification.domain.entities import Notification
    from src.notification_bc.notification.domain.enums import EventType
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )

    session = SessionLocal()
    try:
        repo = AuditRepository(session)

        # Fetch all entries matching filters (no pagination)
        query_filters = dict(filters)
        query_filters["page"] = 1
        query_filters["page_size"] = 100000
        entries, total = repo.find_all(company_id, query_filters)

        task_id = self.request.id or "unknown"

        if export_format == "csv":
            content_bytes = _generate_csv(entries)
            ext = "csv"
        else:
            content_bytes = _generate_pdf(entries, company_id, total)
            ext = "pdf"

        storage_key = f"audit-exports/{company_id}/{task_id}.{ext}"
        storage = S3StorageService()
        storage.upload(storage_key, content_bytes)

        # Create notification
        notif = Notification.create(
            user_id=requested_by,
            company_id=company_id,
            event_type=EventType.AUDIT_EXPORT_READY.value,
            title="Audit export ready",
            body=(
                f"Your audit log export ({ext.upper()})"
                " is ready for download"
            ),
            data={"storage_key": storage_key},
        )
        NotificationRepository(session).save(notif)

        session.commit()
        logger.info(
            "Audit export completed for company %s: %s (%d entries)",
            company_id,
            storage_key,
            total,
        )

    except Exception as exc:
        session.rollback()
        logger.exception(
            "Audit export failed for company %s", company_id
        )
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(
    name="core.tasks.audit.verify_audit_integrity",
    bind=True,
    max_retries=3,
)
def verify_audit_integrity(
    self,
    company_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
):
    """Verify integrity of audit entries by recomputing hashes."""
    from datetime import datetime, timezone

    from core.database import SessionLocal
    from src.audit_bc.audit.domain.entities import AuditEntry
    from src.audit_bc.audit.infrastructure.repository import AuditRepository

    session = SessionLocal()
    try:
        repo = AuditRepository(session)

        if date_from:
            dt_from = datetime.fromisoformat(date_from)
        else:
            dt_from = datetime(2000, 1, 1, tzinfo=timezone.utc)

        if date_to:
            dt_to = datetime.fromisoformat(date_to)
        else:
            dt_to = datetime.now(timezone.utc)

        total_checked = 0
        valid_count = 0
        invalid_count = 0
        first_invalid_entry_id = None
        page = 1
        page_size = 1000

        while True:
            entries = repo.find_entries_for_verification(
                company_id, dt_from, dt_to, page, page_size
            )
            if not entries:
                break

            for entry in entries:
                total_checked += 1
                expected = AuditEntry.compute_hash(
                    company_id=entry.company_id,
                    actor_id=entry.actor_id,
                    action=entry.action,
                    resource_type=entry.resource_type,
                    resource_id=entry.resource_id,
                    created_at=entry.created_at,  # type: ignore[arg-type]
                )
                if expected == entry.hash:
                    valid_count += 1
                else:
                    invalid_count += 1
                    if first_invalid_entry_id is None:
                        first_invalid_entry_id = entry.id

            page += 1

        logger.info(
            "Integrity check for company %s: %d checked, "
            "%d valid, %d invalid",
            company_id,
            total_checked,
            valid_count,
            invalid_count,
        )

        return {
            "total_checked": total_checked,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "first_invalid_entry_id": first_invalid_entry_id,
        }

    except Exception as exc:
        session.rollback()
        logger.exception(
            "Integrity check failed for company %s", company_id
        )
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(
    name="core.tasks.audit.retention_purge",
    bind=True,
    max_retries=3,
)
def retention_purge(self):
    """Purge audit entries older than retention policy cutoff."""
    from datetime import datetime, timezone

    from dateutil.relativedelta import relativedelta

    from core.database import SessionLocal
    from src.audit_bc.audit.domain.entities import AuditEntry
    from src.audit_bc.audit.infrastructure.repository import AuditRepository

    session = SessionLocal()
    try:
        repo = AuditRepository(session)
        policies = repo.find_all_retention_policies()

        for policy in policies:
            cutoff = datetime.now(timezone.utc) - relativedelta(
                months=policy.retention_months
            )

            # Count entries to purge (approximate)
            entries_to_purge, _ = repo.find_all(
                policy.company_id,
                {"page": 1, "page_size": 1, "date_to": cutoff},
            )

            count = repo.delete_entries_before(
                policy.company_id, cutoff
            )

            if count > 0:
                # Create summary audit entry documenting the purge
                summary = AuditEntry.create(
                    company_id=policy.company_id,
                    actor_id=None,
                    actor_email="system",
                    action="audit.retention_purge",
                    resource_type="audit_entry",
                    resource_id=None,
                    http_method="SYSTEM",
                    http_path="retention_purge",
                    ip_address=None,
                    user_agent=None,
                    request_data={
                        "purged_count": count,
                        "cutoff_date": cutoff.isoformat(),
                        "retention_months": policy.retention_months,
                    },
                    response_status=200,
                )
                repo.save(summary)

                logger.info(
                    "Purged %d audit entries for company %s "
                    "(retention: %d months, cutoff: %s)",
                    count,
                    policy.company_id,
                    policy.retention_months,
                    cutoff.isoformat(),
                )

        session.commit()

    except Exception as exc:
        session.rollback()
        logger.exception("Retention purge failed")
        raise self.retry(exc=exc)
    finally:
        session.close()


def _generate_csv(entries) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID",
        "Timestamp",
        "Actor Email",
        "Action",
        "Resource Type",
        "Resource ID",
        "HTTP Method",
        "HTTP Path",
        "Response Status",
        "IP Address",
        "User Agent",
        "Hash",
    ])
    for e in entries:
        writer.writerow([
            e.id,
            e.created_at.isoformat() if e.created_at else "",
            e.actor_email,
            e.action,
            e.resource_type,
            e.resource_id or "",
            e.http_method,
            e.http_path,
            e.response_status,
            e.ip_address or "",
            e.user_agent or "",
            e.hash,
        ])
    return output.getvalue().encode("utf-8")


def _generate_pdf(entries, company_id: str, total: int) -> bytes:
    from datetime import datetime, timezone

    from core.tasks.reports import _get_html_class

    template = _jinja_env.get_template("reports/audit_export.html")
    html_content = template.render(
        title="Audit Log Export",
        company_id=company_id,
        total_entries=total,
        generated_at=datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        ),
        entries=[
            {
                "timestamp": (
                    e.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    if e.created_at
                    else ""
                ),
                "actor_email": e.actor_email,
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id or "",
                "http_method": e.http_method,
                "response_status": e.response_status,
                "ip_address": e.ip_address or "",
                "hash": e.hash[:16] + "...",
            }
            for e in entries
        ],
    )

    html_cls = _get_html_class()
    result: bytes = html_cls(string=html_content).write_pdf()
    return result
