import logging
from datetime import UTC, datetime

from sqlalchemy import select

from core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="core.tasks.maintenance.send_maintenance_reminders",
)
def send_maintenance_reminders() -> int:
    """Send reminder notifications for maintenance due in 48h."""
    from core.database import SessionLocal
    from src.maintenance_bc.maintenance_record.infrastructure.models import (
        MaintenanceRecordModel,
    )
    from src.maintenance_bc.maintenance_record.infrastructure.repository import (
        MaintenanceRecordRepository,
    )
    from src.notification_bc.notification.domain.entities import (
        Notification,
    )
    from src.notification_bc.notification.domain.enums import (
        EventType,
    )
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )

    session = SessionLocal()
    sent = 0
    try:
        record_repo = MaintenanceRecordRepository(session)
        notif_repo = NotificationRepository(session)

        company_ids = session.execute(
            select(MaintenanceRecordModel.company_id).distinct(),
        ).scalars().all()

        for company_id in company_ids:
            due_records = record_repo.find_due_within_hours(
                company_id=company_id,
                hours=48,
            )
            for record in due_records:
                if not record.technician_id:
                    continue
                notif = Notification.create(
                    user_id=record.technician_id,
                    company_id=record.company_id,
                    event_type=EventType.MAINTENANCE_DUE.value,
                    title="Maintenance due soon",
                    body=record.title,
                    data={
                        "maintenance_id": record.id,
                        "asset_id": record.asset_id,
                        "scheduled_at": (
                            record.scheduled_at.isoformat() if record.scheduled_at else None
                        ),
                        "technician_id": record.technician_id,
                    },
                )
                notif_repo.save(notif)
                record.mark_reminder_sent()
                record_repo.save(record)
                sent += 1

        session.commit()
        logger.info("Sent %d maintenance reminders", sent)
        return sent
    except Exception:
        session.rollback()
        logger.exception("Maintenance reminder task failed")
        raise
    finally:
        session.close()


@celery_app.task(
    name="core.tasks.maintenance.check_overdue_maintenance",
)
def check_overdue_maintenance() -> int:
    """Send alerts for overdue scheduled maintenance records."""
    from core.database import SessionLocal
    from src.maintenance_bc.maintenance_record.infrastructure.models import (
        MaintenanceRecordModel,
    )
    from src.maintenance_bc.maintenance_record.infrastructure.repository import (
        MaintenanceRecordRepository,
    )
    from src.notification_bc.notification.domain.entities import (
        Notification,
    )
    from src.notification_bc.notification.domain.enums import (
        EventType,
    )
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )

    session = SessionLocal()
    sent = 0
    try:
        record_repo = MaintenanceRecordRepository(session)
        notif_repo = NotificationRepository(session)

        company_ids = session.execute(
            select(MaintenanceRecordModel.company_id).distinct(),
        ).scalars().all()

        for company_id in company_ids:
            overdue_records = record_repo.find_overdue(
                company_id=company_id,
            )
            for record in overdue_records:
                if not record.technician_id:
                    continue
                notif = Notification.create(
                    user_id=record.technician_id,
                    company_id=record.company_id,
                    event_type=EventType.MAINTENANCE_OVERDUE.value,
                    title="Maintenance overdue",
                    body=record.title,
                    data={
                        "maintenance_id": record.id,
                        "asset_id": record.asset_id,
                        "scheduled_at": (
                            record.scheduled_at.isoformat() if record.scheduled_at else None
                        ),
                        "technician_id": record.technician_id,
                    },
                )
                notif_repo.save(notif)
                record.mark_overdue_alert_sent()
                record_repo.save(record)
                sent += 1

        session.commit()
        logger.info("Sent %d maintenance overdue alerts", sent)
        return sent
    except Exception:
        session.rollback()
        logger.exception("Maintenance overdue task failed")
        raise
    finally:
        session.close()


@celery_app.task(
    name="core.tasks.maintenance.generate_recurring_maintenance",
)
def generate_recurring_maintenance() -> int:
    """Generate maintenance records for due active recurring plans."""
    from core.database import SessionLocal
    from src.maintenance_bc.maintenance_record.domain.entities import (
        MaintenanceRecord,
    )
    from src.maintenance_bc.maintenance_record.infrastructure.models import (
        MaintenanceRecordModel,
    )
    from src.maintenance_bc.maintenance_record.infrastructure.repository import (
        MaintenanceRecordRepository,
    )
    from src.maintenance_bc.maintenance_template.application.services.recurrence import (
        compute_next_due,
    )
    from src.maintenance_bc.maintenance_template.infrastructure.models import (
        MaintenancePlanModel,
    )
    from src.maintenance_bc.maintenance_template.infrastructure.repository import (
        MaintenancePlanRepository,
        MaintenanceTemplateRepository,
    )

    session = SessionLocal()
    generated = 0
    try:
        now = datetime.now(UTC)
        plan_repo = MaintenancePlanRepository(session)
        template_repo = MaintenanceTemplateRepository(session)
        record_repo = MaintenanceRecordRepository(session)

        company_ids = session.execute(
            select(MaintenancePlanModel.company_id).distinct(),
        ).scalars().all()

        for company_id in company_ids:
            due_plans = plan_repo.find_due_plans(
                company_id=company_id,
                due_before=now,
            )
            if not due_plans:
                continue

            template_map = template_repo.find_by_ids(
                [p.template_id for p in due_plans],
                company_id=company_id,
            )
            for plan in due_plans:
                template = template_map.get(plan.template_id)
                if (
                    template is None
                    or not template.is_active
                    or template.recurrence_frequency is None
                ):
                    continue

                record = MaintenanceRecord.create(
                    company_id=company_id,
                    asset_id=plan.asset_id,
                    title=template.name,
                    priority=template.default_priority,
                    description=template.description,
                    template_id=template.id,
                    plan_id=plan.id,
                    checklist_items=[i.title for i in template.checklist_items],
                    scheduled_at=plan.next_due_at,
                )
                record_repo.save(record)

                next_due = compute_next_due(
                    base=plan.next_due_at,
                    frequency=template.recurrence_frequency,
                    interval=template.recurrence_interval,
                )
                plan.update_next_due(
                    next_due_at=next_due,
                    last_generated_at=now,
                )
                plan_repo.save(plan)
                generated += 1

        session.commit()
        logger.info(
            "Generated %d recurring maintenance records",
            generated,
        )
        return generated
    except Exception:
        session.rollback()
        logger.exception("Recurring maintenance generation task failed")
        raise
    finally:
        session.close()
