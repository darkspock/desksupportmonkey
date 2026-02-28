import logging
from datetime import date, timedelta

from core.celery import celery_app

logger = logging.getLogger(__name__)

RENEWAL_REMINDER_DAYS = [60, 30, 7]
CONCENTRATION_THRESHOLD = 0.40


@celery_app.task(
    name="core.tasks.vendor_contracts.expire_active_contracts",
)
def expire_active_contracts() -> int:
    """Transition active contracts past their end_date to expired status."""
    from core.database import SessionLocal
    from src.procurement_bc.vendor.domain.enums import ContractStatus
    from src.procurement_bc.vendor.infrastructure.repository import (
        VendorContractRepository,
    )

    session = SessionLocal()
    expired_count = 0
    try:
        contract_repo = VendorContractRepository(session)
        contracts = contract_repo.find_expired_active_contracts()

        for contract in contracts:
            contract.change_status(ContractStatus.EXPIRED)
            contract_repo.save(contract)
            expired_count += 1
            logger.info(
                "Contract %s auto-expired (end_date: %s)",
                contract.id, contract.end_date,
            )

        session.commit()
        logger.info(
            "Auto-expired %d contracts", expired_count,
        )
        return expired_count
    except Exception:
        session.rollback()
        logger.exception("Contract auto-expiry task failed")
        raise
    finally:
        session.close()


@celery_app.task(
    name="core.tasks.vendor_contracts.send_contract_renewal_reminders",
)
def send_contract_renewal_reminders() -> int:
    """Send renewal reminders at 60/30/7 days before contract renewal_date."""
    from sqlalchemy import select

    from core.database import SessionLocal
    from src.auth_bc.user.infrastructure.repository import UserRepository
    from src.notification_bc.notification.domain.entities import Notification
    from src.notification_bc.notification.domain.enums import EventType
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )
    from src.procurement_bc.vendor.domain.enums import ContractStatus
    from src.procurement_bc.vendor.infrastructure.models import (
        VendorContractModel,
        VendorModel,
    )

    session = SessionLocal()
    sent = 0
    try:
        notif_repo = NotificationRepository(session)
        user_repo = UserRepository(session)
        today = date.today()

        for days in RENEWAL_REMINDER_DAYS:
            target_date = today + timedelta(days=days)
            contracts = (
                session.execute(
                    select(VendorContractModel)
                    .where(
                        VendorContractModel.status == ContractStatus.ACTIVE.value,
                        VendorContractModel.is_deleted.is_(False),
                        VendorContractModel.renewal_date == target_date,
                    )
                )
                .scalars()
                .all()
            )

            for contract in contracts:
                # Idempotency: check if reminder already sent for this contract+date
                existing = notif_repo.find_by_data_key(
                    event_type=EventType.CONTRACT_RENEWAL_REMINDER.value,
                    data_key="contract_id",
                    data_value=contract.id,
                    date_check=today,
                )
                if existing:
                    continue

                vendor = session.execute(
                    select(VendorModel).where(VendorModel.id == contract.vendor_id)
                ).scalar_one_or_none()
                vendor_name = vendor.name if vendor else "Unknown"

                admin_ids = user_repo.find_admin_ids_by_company(
                    contract.company_id,
                )
                for admin_id in admin_ids:
                    notif = Notification.create(
                        user_id=admin_id,
                        company_id=contract.company_id,
                        event_type=EventType.CONTRACT_RENEWAL_REMINDER.value,
                        title=f"Contract renewal in {days} days",
                        body=f"{contract.title} ({vendor_name}) renews on {target_date}",
                        data={
                            "contract_id": contract.id,
                            "vendor_id": contract.vendor_id,
                            "vendor_name": vendor_name,
                            "renewal_date": str(target_date),
                            "days_remaining": days,
                        },
                    )
                    notif_repo.save(notif)
                    sent += 1

        session.commit()
        logger.info("Sent %d contract renewal reminders", sent)
        return sent
    except Exception:
        session.rollback()
        logger.exception("Contract renewal reminder task failed")
        raise
    finally:
        session.close()


@celery_app.task(
    name="core.tasks.vendor_contracts.check_concentration_risk",
)
def check_concentration_risk() -> int:
    """Alert admins when vendor concentration risk exceeds threshold."""
    from sqlalchemy import select

    from core.database import SessionLocal
    from src.auth_bc.user.infrastructure.repository import UserRepository
    from src.notification_bc.notification.domain.entities import Notification
    from src.notification_bc.notification.domain.enums import EventType
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )
    from src.procurement_bc.vendor.application.queries.concentration_risk import (
        ConcentrationRiskQuery,
        ConcentrationRiskQueryHandler,
    )
    from src.procurement_bc.vendor.infrastructure.models import VendorModel
    from src.procurement_bc.vendor.infrastructure.repository import (
        VendorDependencyRepository,
        VendorRepository,
    )

    session = SessionLocal()
    sent = 0
    try:
        notif_repo = NotificationRepository(session)
        user_repo = UserRepository(session)
        dep_repo = VendorDependencyRepository(session)
        vendor_repo = VendorRepository(session)
        today = date.today()

        company_ids = (
            session.execute(select(VendorModel.company_id).distinct())
            .scalars()
            .all()
        )

        for company_id in company_ids:
            handler = ConcentrationRiskQueryHandler(
                dependency_repo=dep_repo,
                vendor_repo=vendor_repo,
            )
            items = handler.handle(
                ConcentrationRiskQuery(company_id=company_id),
            )

            above = [i for i in items if i.is_above_threshold]
            if not above:
                continue

            # Idempotency: check if already alerted today
            existing = notif_repo.find_by_data_key(
                event_type=EventType.CONCENTRATION_RISK_ALERT.value,
                data_key="company_id",
                data_value=company_id,
                date_check=today,
            )
            if existing:
                continue

            vendor_names = ", ".join(i.vendor_name for i in above[:3])
            admin_ids = user_repo.find_admin_ids_by_company(company_id)
            for admin_id in admin_ids:
                notif = Notification.create(
                    user_id=admin_id,
                    company_id=company_id,
                    event_type=EventType.CONCENTRATION_RISK_ALERT.value,
                    title="Concentration risk alert",
                    body=f"{len(above)} vendor(s) exceed threshold: {vendor_names}",
                    data={
                        "company_id": company_id,
                        "vendors_above_threshold": len(above),
                        "check_date": str(today),
                    },
                )
                notif_repo.save(notif)
                sent += 1

        session.commit()
        logger.info("Sent %d concentration risk alerts", sent)
        return sent
    except Exception:
        session.rollback()
        logger.exception("Concentration risk check task failed")
        raise
    finally:
        session.close()


@celery_app.task(
    name="core.tasks.vendor_contracts.check_stale_assessments",
)
def check_stale_assessments() -> int:
    """Alert admins when vendor assessments are overdue for review."""
    from sqlalchemy import select

    from core.database import SessionLocal
    from src.auth_bc.user.infrastructure.repository import UserRepository
    from src.notification_bc.notification.domain.entities import Notification
    from src.notification_bc.notification.domain.enums import EventType
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )
    from src.procurement_bc.vendor.infrastructure.models import VendorModel
    from src.procurement_bc.vendor.infrastructure.repository import (
        VendorRiskAssessmentRepository,
    )

    session = SessionLocal()
    sent = 0
    try:
        notif_repo = NotificationRepository(session)
        user_repo = UserRepository(session)
        assessment_repo = VendorRiskAssessmentRepository(session)
        today = date.today()

        company_ids = (
            session.execute(select(VendorModel.company_id).distinct())
            .scalars()
            .all()
        )

        for company_id in company_ids:
            stale_vendor_ids = assessment_repo.find_vendors_with_stale_assessments(
                company_id=company_id, as_of=today,
            )
            if not stale_vendor_ids:
                continue

            for vendor_id in stale_vendor_ids:
                # Idempotency: check if already alerted today for this vendor
                existing = notif_repo.find_by_data_key(
                    event_type=EventType.VENDOR_ASSESSMENT_OVERDUE.value,
                    data_key="vendor_id",
                    data_value=vendor_id,
                    date_check=today,
                )
                if existing:
                    continue

                vendor = session.execute(
                    select(VendorModel).where(VendorModel.id == vendor_id)
                ).scalar_one_or_none()
                vendor_name = vendor.name if vendor else "Unknown"

                admin_ids = user_repo.find_admin_ids_by_company(company_id)
                for admin_id in admin_ids:
                    notif = Notification.create(
                        user_id=admin_id,
                        company_id=company_id,
                        event_type=EventType.VENDOR_ASSESSMENT_OVERDUE.value,
                        title="Vendor assessment overdue",
                        body=f"Risk assessment for {vendor_name} is overdue for review",
                        data={
                            "vendor_id": vendor_id,
                            "vendor_name": vendor_name,
                            "check_date": str(today),
                        },
                    )
                    notif_repo.save(notif)
                    sent += 1

        session.commit()
        logger.info("Sent %d stale assessment alerts", sent)
        return sent
    except Exception:
        session.rollback()
        logger.exception("Stale assessment check task failed")
        raise
    finally:
        session.close()


@celery_app.task(
    name="core.tasks.vendor_contracts.export_vendor_risk_report",
    bind=True,
    max_retries=3,
)
def export_vendor_risk_report(
    self,
    company_id: str,
    requested_by: str,
    export_format: str,
):
    """Generate vendor risk export (PDF or CSV) and upload to MinIO."""
    from core.database import SessionLocal
    from core.storage import S3StorageService
    from src.notification_bc.notification.domain.entities import Notification
    from src.notification_bc.notification.domain.enums import EventType
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )
    from src.procurement_bc.vendor.application.commands.export_vendor_risk import (
        ExportVendorRiskCommand,
        ExportVendorRiskCommandHandler,
    )
    from src.procurement_bc.vendor.infrastructure.repository import (
        VendorContractRepository,
        VendorDependencyRepository,
        VendorRiskAssessmentRepository,
        VendorRepository,
    )

    session = SessionLocal()
    try:
        task_id = self.request.id or "unknown"
        handler = ExportVendorRiskCommandHandler(
            vendor_repo=VendorRepository(session),
            contract_repo=VendorContractRepository(session),
            assessment_repo=VendorRiskAssessmentRepository(session),
            dependency_repo=VendorDependencyRepository(session),
        )
        content_bytes = handler.handle(
            ExportVendorRiskCommand(
                company_id=company_id,
                export_format=export_format,
                requested_by=requested_by,
                task_id=task_id,
            ),
        )

        ext = "csv" if export_format == "csv" else "pdf"
        content_type = (
            "text/csv" if ext == "csv" else "application/pdf"
        )
        storage_key = f"vendor-risk-exports/{company_id}/{task_id}.{ext}"
        storage = S3StorageService()
        storage.upload(storage_key, content_bytes, content_type=content_type)

        notif = Notification.create(
            user_id=requested_by,
            company_id=company_id,
            event_type=EventType.REPORT_READY.value,
            title="Vendor risk export ready",
            body=f"Your vendor risk export ({ext.upper()}) is ready for download",
            data={"storage_key": storage_key},
        )
        NotificationRepository(session).save(notif)

        session.commit()
        logger.info(
            "Vendor risk export completed for company %s: %s",
            company_id, storage_key,
        )
    except Exception as exc:
        session.rollback()
        logger.exception(
            "Vendor risk export failed for company %s", company_id,
        )
        raise self.retry(exc=exc)
    finally:
        session.close()
