import logging
import os
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader

from core.celery import celery_app
from core.config import settings

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")

TEMPLATE_MAP = {
    "asset_inventory": "reports/asset_inventory.html",
    "request_summary": "reports/request_summary.html",
    "technician_performance": "reports/technician_performance.html",
    "department_spending": "reports/department_spending.html",
    "sla_compliance": "reports/sla_compliance.html",
}

_jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
_jinja_env.globals["brand_name"] = settings.BRAND_NAME
HTML = None


class ReportDependencyError(Exception):
    """Raised when report system dependencies (WeasyPrint libs) are unavailable."""


def _get_html_class():
    global HTML
    if HTML is not None:
        return HTML
    try:
        from weasyprint import HTML as WeasyHTML
    except (ImportError, OSError) as exc:
        raise ReportDependencyError(
            "Report generation unavailable: missing WeasyPrint system libraries "
            "(e.g. libgobject/pango/cairo)."
        ) from exc
    HTML = WeasyHTML
    return HTML


@celery_app.task(
    name="core.tasks.reports.generate_report",
    bind=True,
    max_retries=settings.report.REPORT_MAX_RETRIES,
)
def generate_report(self, report_id: str):
    """Generate a PDF report asynchronously."""
    from core.database import SessionLocal
    from core.storage import S3StorageService
    from core.tasks.report_data import (
        collect_asset_inventory,
        collect_department_spending,
        collect_request_summary,
        collect_sla_compliance,
        collect_technician_performance,
    )
    from src.report_bc.report.domain.enums import ReportStatus
    from src.report_bc.report.infrastructure.repository import ReportRepository

    DATA_COLLECTORS = {
        "asset_inventory": collect_asset_inventory,
        "request_summary": collect_request_summary,
        "technician_performance": collect_technician_performance,
        "department_spending": collect_department_spending,
        "sla_compliance": collect_sla_compliance,
    }

    session = SessionLocal()
    repo = None
    try:
        repo = ReportRepository(session)
        report = repo.find_by_id_any_company(report_id)
        if not report:
            logger.error("Report not found: %s", report_id)
            return

        # 1. Update status to processing
        repo.update_status(report_id, ReportStatus.PROCESSING)
        session.commit()

        # 2. Collect data
        collector = DATA_COLLECTORS[report.type.value]
        data = collector(report.company_id, report.parameters, session)

        # 3. Render HTML
        template_name = TEMPLATE_MAP[report.type.value]
        template = _jinja_env.get_template(template_name)
        html_content = template.render(
            title=report.type.value.replace("_", " ").title(),
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            **data,
        )

        # 4. Convert to PDF
        html_cls = _get_html_class()
        pdf_bytes = html_cls(string=html_content).write_pdf()

        # 5. Upload to S3
        storage_key = f"reports/{report.company_id}/{report.id}.pdf"
        storage = S3StorageService()
        storage.upload(storage_key, pdf_bytes)

        # 6. Update report to completed
        repo.update_status(report_id, ReportStatus.COMPLETED, storage_key=storage_key)

        # 7. Create notification for the requester
        from src.notification_bc.notification.domain.entities import Notification
        from src.notification_bc.notification.domain.enums import EventType
        from src.notification_bc.notification.infrastructure.repository import NotificationRepository

        notif = Notification.create(
            user_id=report.requested_by,
            company_id=report.company_id,
            event_type=EventType.REPORT_READY.value,
            title="Report ready",
            body=f"{report.type.value.replace('_', ' ').title()} report is ready for download",
            data={"report_id": report.id},
        )
        notif_repo = NotificationRepository(session)
        notif_repo.save(notif)

        session.commit()
        logger.info("Report %s completed: %s", report_id, storage_key)

    except ReportDependencyError as exc:
        session.rollback()
        if repo is not None:
            try:
                repo.update_status(report_id, ReportStatus.FAILED, error_message=str(exc))
                session.commit()
            except Exception:
                session.rollback()
                logger.exception("Failed to update report status for %s", report_id)
        logger.error("Report generation dependency missing for %s: %s", report_id, exc)
        return
    except Exception as exc:
        session.rollback()
        if repo is not None:
            try:
                repo.update_status(report_id, ReportStatus.FAILED, error_message=str(exc))
                session.commit()
            except Exception:
                session.rollback()
                logger.exception("Failed to update report status for %s", report_id)
        logger.exception("Report generation failed for %s", report_id)
        raise self.retry(exc=exc)
    finally:
        session.close()


def _format_cents(cents: int, currency: str = "USD") -> str:
    return f"{currency} {cents / 100:,.2f}"


@celery_app.task(
    name="core.tasks.reports.generate_po_pdf",
    bind=True,
    max_retries=2,
)
def generate_po_pdf(self, po_id: str, company_id: str) -> str | None:
    """Generate a PDF for a purchase order and upload to MinIO."""
    from core.database import SessionLocal
    from core.storage import S3StorageService
    from src.company_bc.company.infrastructure.repository import CompanyRepository
    from src.procurement_bc.purchase_order.infrastructure.repository import (
        PurchaseOrderRepository,
    )

    session = SessionLocal()
    try:
        po_repo = PurchaseOrderRepository(session)
        company_repo = CompanyRepository(session)

        po = po_repo.find_by_id(po_id, company_id)
        if not po:
            logger.error("PO not found for PDF generation: %s", po_id)
            return None

        company = company_repo.find_by_id(company_id)
        company_name = company.name if company else "Unknown"
        currency = po.currency

        template_data = {
            "title": f"Purchase Order — {po.po_number}",
            "company_name": company_name,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "po_number": po.po_number,
            "status": po.status.value.replace("_", " ").title(),
            "vendor_name": po.vendor_name,
            "total_amount": _format_cents(po.total_amount_cents, currency),
            "currency": currency,
            "created_at": po.created_at.strftime("%Y-%m-%d") if po.created_at else "—",
            "approved_at": po.approved_at.strftime("%Y-%m-%d") if po.approved_at else None,
            "ordered_at": po.ordered_at.strftime("%Y-%m-%d") if po.ordered_at else None,
            "notes": po.notes,
            "items": [
                {
                    "description": item.description,
                    "asset_type": (item.asset_type or "").replace("_", " ").title() if item.asset_type else None,
                    "quantity": item.quantity,
                    "unit_cost": _format_cents(item.unit_cost_cents, currency),
                    "total_cost": _format_cents(item.total_cost_cents, currency),
                }
                for item in po.items
            ],
        }

        template = _jinja_env.get_template("reports/purchase_order.html")
        html_content = template.render(**template_data)

        html_cls = _get_html_class()
        pdf_bytes = html_cls(string=html_content).write_pdf()

        storage_key = f"po-pdfs/{company_id}/{po_id}.pdf"
        storage = S3StorageService()
        storage.upload(storage_key, pdf_bytes)

        session.commit()
        logger.info("PO PDF generated: %s → %s", po.po_number, storage_key)
        return storage_key

    except ReportDependencyError as exc:
        logger.error("PO PDF dependency missing for %s: %s", po_id, exc)
        return None
    except Exception as exc:
        logger.exception("PO PDF generation failed for %s", po_id)
        raise self.retry(exc=exc)
    finally:
        session.close()
