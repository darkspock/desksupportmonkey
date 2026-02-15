import logging

from core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="core.tasks.cleanup.cleanup_magic_links")
def cleanup_magic_links(days: int = 7) -> int:
    """Delete magic links older than N days."""
    from core.database import SessionLocal
    from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository

    session = SessionLocal()
    try:
        repo = MagicLinkRepository(session)
        count = repo.delete_older_than(days)
        session.commit()
        logger.info("Cleaned up %d magic links older than %d days", count, days)
        return count
    except Exception as e:
        session.rollback()
        logger.error("Magic link cleanup failed: %s", str(e))
        raise
    finally:
        session.close()
