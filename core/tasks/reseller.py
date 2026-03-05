import logging
from datetime import datetime, timedelta

from core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="core.tasks.reseller.expire_demo_accounts")
def expire_demo_accounts() -> dict:
    """Suspend demos expired >14 days, deactivate demos expired >44 days.

    Uses Company.plan='demo' + trial_ends_at as the primary source for expiration.
    """
    from core.database import SessionLocal
    from sqlalchemy import select
    from src.company_bc.company.domain.enums import CompanyStatus
    from src.company_bc.company.infrastructure.models import CompanyModel
    from src.company_bc.company.infrastructure.repository import CompanyRepository

    session = SessionLocal()
    try:
        now = datetime.utcnow()
        company_repo = CompanyRepository(session)

        # Phase 1: Suspend active demo companies past their trial_ends_at
        expired_stmt = (
            select(CompanyModel.id)
            .where(CompanyModel.plan == "demo")
            .where(CompanyModel.status == "active")
            .where(CompanyModel.trial_ends_at <= now)
        )
        expired_ids = session.execute(expired_stmt).scalars().all()
        suspended_count = 0
        for company in company_repo.find_by_ids(expired_ids):
            if company.status == CompanyStatus.ACTIVE:
                company.change_status(CompanyStatus.SUSPENDED)
                company_repo.save(company)
                suspended_count += 1

        # Phase 2: Deactivate suspended demos past purge window (30 days after trial_ends_at)
        purge_cutoff = now - timedelta(days=30)
        purgeable_stmt = (
            select(CompanyModel.id)
            .where(CompanyModel.plan == "demo")
            .where(CompanyModel.status == "suspended")
            .where(CompanyModel.trial_ends_at <= purge_cutoff)
        )
        purgeable_ids = session.execute(purgeable_stmt).scalars().all()
        deactivated_count = 0
        for company in company_repo.find_by_ids(purgeable_ids):
            if company.status == CompanyStatus.SUSPENDED:
                company.change_status(CompanyStatus.DEACTIVATED)
                company_repo.save(company)
                deactivated_count += 1

        session.commit()
        logger.info("Demo expiry: suspended=%d, deactivated=%d", suspended_count, deactivated_count)
        return {"suspended": suspended_count, "deactivated": deactivated_count}
    except Exception as e:
        session.rollback()
        logger.error("Demo expiry task failed: %s", str(e))
        raise
    finally:
        session.close()
