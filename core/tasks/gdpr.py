import hashlib
import io
import json
import logging
import zipfile
from datetime import datetime, timezone

from core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="core.tasks.gdpr.gdpr_data_export",
    bind=True,
    max_retries=3,
)
def gdpr_data_export(self, gdpr_request_id: str):
    """Collect all user data and generate a ZIP export."""
    from sqlalchemy import select

    from core.database import SessionLocal
    from core.storage import S3StorageService
    from src.asset_bc.asset.infrastructure.models import AssetModel
    from src.audit_bc.audit.infrastructure.models import AuditEntryModel
    from src.audit_bc.audit.infrastructure.repository import AuditRepository
    from src.auth_bc.user.infrastructure.repository import UserRepository
    from src.notification_bc.notification.domain.entities import Notification
    from src.notification_bc.notification.domain.enums import EventType
    from src.notification_bc.notification.infrastructure.models import (
        NotificationModel,
    )
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )
    from src.request_bc.request.infrastructure.models import (
        RequestCommentModel,
        ServiceRequestModel,
    )

    session = SessionLocal()
    try:
        audit_repo = AuditRepository(session)
        user_repo = UserRepository(session)

        request = audit_repo.find_gdpr_request_by_id(gdpr_request_id)
        if request is None:
            logger.error("GDPR request %s not found", gdpr_request_id)
            return

        request.start_processing()
        audit_repo.save_gdpr_request(request)
        session.flush()

        user = user_repo.find_by_id(request.target_user_id)
        if user is None:
            request.fail("Target user not found")
            audit_repo.save_gdpr_request(request)
            session.commit()
            return

        # Collect data
        user_data = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "company_id": user.company_id,
            "is_active": user.is_active,
            "created_at": (
                user.created_at.isoformat() if user.created_at else None
            ),
        }

        # Assets
        assets = session.execute(
            select(AssetModel).where(
                AssetModel.assigned_to == user.id
            )
        ).scalars().all()
        assets_data = [
            {
                "id": a.id,
                "type": a.type,
                "brand": a.brand,
                "model": a.model,
                "serial_number": a.serial_number,
                "status": a.status,
            }
            for a in assets
        ]

        # Requests
        requests = session.execute(
            select(ServiceRequestModel).where(
                ServiceRequestModel.created_by == user.id
            )
        ).scalars().all()
        requests_data = [
            {
                "id": r.id,
                "title": r.title,
                "status": r.status,
                "created_at": (
                    r.created_at.isoformat() if r.created_at else None
                ),
            }
            for r in requests
        ]

        # Comments
        comments = session.execute(
            select(RequestCommentModel).where(
                RequestCommentModel.author_id == user.id
            )
        ).scalars().all()
        comments_data = [
            {
                "id": c.id,
                "request_id": c.request_id,
                "body": c.body,
                "created_at": (
                    c.created_at.isoformat() if c.created_at else None
                ),
            }
            for c in comments
        ]

        # Notifications
        notifications = session.execute(
            select(NotificationModel).where(
                NotificationModel.user_id == user.id
            )
        ).scalars().all()
        notifications_data = [
            {
                "id": n.id,
                "event_type": n.event_type,
                "title": n.title,
                "created_at": (
                    n.created_at.isoformat() if n.created_at else None
                ),
            }
            for n in notifications
        ]

        # Audit entries
        audit_entries = session.execute(
            select(AuditEntryModel).where(
                AuditEntryModel.actor_id == user.id
            )
        ).scalars().all()
        audit_data = [
            {
                "id": a.id,
                "action": a.action,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "created_at": (
                    a.created_at.isoformat() if a.created_at else None
                ),
            }
            for a in audit_entries
        ]

        # Generate ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "user_profile.json",
                json.dumps(user_data, indent=2),
            )
            zf.writestr(
                "assets.json",
                json.dumps(assets_data, indent=2),
            )
            zf.writestr(
                "requests.json",
                json.dumps(requests_data, indent=2),
            )
            zf.writestr(
                "comments.json",
                json.dumps(comments_data, indent=2),
            )
            zf.writestr(
                "notifications.json",
                json.dumps(notifications_data, indent=2),
            )
            zf.writestr(
                "audit_entries.json",
                json.dumps(audit_data, indent=2),
            )
        zip_bytes = zip_buffer.getvalue()

        # Upload
        storage_key = (
            f"gdpr-exports/{request.company_id}/{request.id}.zip"
        )
        storage = S3StorageService()
        storage.upload(storage_key, zip_bytes)

        request.complete(storage_key=storage_key)
        audit_repo.save_gdpr_request(request)

        # Notification
        notif = Notification.create(
            user_id=request.requested_by,
            company_id=request.company_id,
            event_type=EventType.GDPR_DATA_EXPORT_READY.value,
            title="GDPR data export ready",
            body=(
                f"Data export for {request.target_user_email}"
                " is ready for download"
            ),
            data={"gdpr_request_id": request.id},
        )
        NotificationRepository(session).save(notif)

        session.commit()
        logger.info(
            "GDPR data export completed: %s", gdpr_request_id
        )

    except Exception as exc:
        session.rollback()
        logger.exception(
            "GDPR data export failed: %s", gdpr_request_id
        )
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(
    name="core.tasks.gdpr.gdpr_anonymize_user",
    bind=True,
    max_retries=3,
)
def gdpr_anonymize_user(self, gdpr_request_id: str):
    """Anonymize a user's personal data across the system."""
    from core.database import SessionLocal
    from src.audit_bc.audit.infrastructure.repository import AuditRepository
    from src.auth_bc.user.infrastructure.repository import UserRepository
    from src.notification_bc.notification.domain.entities import Notification
    from src.notification_bc.notification.domain.enums import EventType
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )

    session = SessionLocal()
    try:
        audit_repo = AuditRepository(session)
        user_repo = UserRepository(session)

        request = audit_repo.find_gdpr_request_by_id(gdpr_request_id)
        if request is None:
            logger.error("GDPR request %s not found", gdpr_request_id)
            return

        request.start_processing()
        audit_repo.save_gdpr_request(request)
        session.flush()

        user = user_repo.find_by_id(request.target_user_id)
        if user is None:
            request.fail("Target user not found")
            audit_repo.save_gdpr_request(request)
            session.commit()
            return

        # Generate anonymized email
        hash6 = hashlib.sha256(user.id.encode()).hexdigest()[:6]
        anonymized_email = f"anonymized-{hash6}@redacted.local"

        # Anonymize user fields
        user.email = anonymized_email
        user.name = "Anonymized User"
        user.password_hash = None
        user.google_id = None
        user.microsoft_id = None
        user.is_anonymized = True
        user.is_active = False
        user_repo.save(user)

        # Bulk update audit entries
        count = audit_repo.anonymize_actor_email(
            user.id, anonymized_email
        )
        logger.info(
            "Anonymized %d audit entries for user %s",
            count,
            request.target_user_id,
        )

        request.complete()
        audit_repo.save_gdpr_request(request)

        # Notification
        notif = Notification.create(
            user_id=request.requested_by,
            company_id=request.company_id,
            event_type=EventType.GDPR_ANONYMIZATION_COMPLETED.value,
            title="GDPR anonymization completed",
            body=(
                f"User {request.target_user_email}"
                " has been anonymized"
            ),
            data={"gdpr_request_id": request.id},
        )
        NotificationRepository(session).save(notif)

        session.commit()
        logger.info(
            "GDPR anonymization completed: %s", gdpr_request_id
        )

    except Exception as exc:
        session.rollback()
        logger.exception(
            "GDPR anonymization failed: %s", gdpr_request_id
        )
        raise self.retry(exc=exc)
    finally:
        session.close()
