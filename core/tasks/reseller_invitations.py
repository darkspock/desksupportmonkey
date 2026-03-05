import logging

from core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="core.tasks.reseller_invitations.expire_pending_invitations")
def expire_pending_invitations() -> dict:
    """Mark PENDING invitations past their expires_at as EXPIRED."""
    from core.database import SessionLocal
    from src.reseller_bc.invitation.domain.enums import InvitationStatus
    from src.reseller_bc.invitation.infrastructure.repository import ResellerInvitationRepository

    session = SessionLocal()
    try:
        repo = ResellerInvitationRepository(session)
        expired = repo.find_expired_pending()
        count = 0
        for invitation in expired:
            invitation.status = InvitationStatus.EXPIRED
            repo.save(invitation)
            count += 1

        session.commit()
        logger.info("Expired %d pending invitations", count)
        return {"expired": count}
    except Exception as e:
        session.rollback()
        logger.error("Expire invitations task failed: %s", str(e))
        raise
    finally:
        session.close()
