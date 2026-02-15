import logging

from fastapi import APIRouter
from sqlalchemy import create_engine, text

from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health_check():
    """Check API and database health."""
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return {"data": {"status": "healthy"}}
    except Exception as e:
        logger.error("Health check failed: %s", str(e))
        return {"data": {"status": "unhealthy", "detail": str(e)}}
