import logging
from datetime import datetime, timedelta

from core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="core.tasks.commission.confirm_commissions")
def confirm_commissions() -> dict:
    """Transition pending commissions to confirmed after 30 days."""
    from core.database import SessionLocal
    from src.reseller_bc.commission.infrastructure.repository import ResellerCommissionRepository

    session = SessionLocal()
    try:
        repo = ResellerCommissionRepository(session)
        cutoff = datetime.utcnow() - timedelta(days=30)
        pending = repo.find_pending_before(before=cutoff)
        confirmed_count = 0
        for commission in pending:
            commission.confirm()
            repo.save(commission)
            confirmed_count += 1
        session.commit()
        logger.info("Commission confirmation: confirmed=%d", confirmed_count)
        return {"confirmed": confirmed_count}
    except Exception as e:
        session.rollback()
        logger.error("Commission confirmation failed: %s", str(e))
        raise
    finally:
        session.close()
