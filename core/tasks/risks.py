import logging

from sqlalchemy import select

from core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="core.tasks.risks.check_overdue_reviews",
)
def check_overdue_reviews() -> int:
    """Send alerts for risks with overdue review dates."""
    from core.database import SessionLocal
    from src.notification_bc.notification.domain.entities import Notification
    from src.notification_bc.notification.domain.enums import EventType
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )
    from src.risk_bc.risk.domain.entities import RiskHistory
    from src.risk_bc.risk.domain.enums import RiskHistoryEventType
    from src.risk_bc.risk.infrastructure.models import RiskModel
    from src.risk_bc.risk.infrastructure.repository import RiskRepository

    session = SessionLocal()
    sent = 0
    try:
        risk_repo = RiskRepository(session)
        notif_repo = NotificationRepository(session)

        company_ids = (
            session.execute(select(RiskModel.company_id).distinct())
            .scalars()
            .all()
        )

        for company_id in company_ids:
            overdue_risks = risk_repo.find_overdue_reviews(
                company_id=company_id,
            )
            for risk in overdue_risks:
                # Check if we already sent an overdue alert for this review period
                history = risk_repo.get_history(risk.id)
                already_alerted = any(
                    h.event_type == RiskHistoryEventType.REVIEW_COMPLETED
                    or (
                        h.metadata
                        and h.metadata.get("review_overdue_alert")
                        and h.metadata.get("next_review_at")
                        == (
                            risk.next_review_at.isoformat()
                            if risk.next_review_at
                            else None
                        )
                    )
                    for h in history
                )
                if already_alerted:
                    continue

                # Determine notification target
                target_id = risk.owner_id or risk.created_by
                notif = Notification.create(
                    user_id=target_id,
                    company_id=risk.company_id,
                    event_type=EventType.RISK_REVIEW_OVERDUE.value,
                    title="Risk review overdue",
                    body=risk.title,
                    data={
                        "risk_id": risk.id,
                        "owner_id": risk.owner_id,
                        "next_review_at": (
                            risk.next_review_at.isoformat()
                            if risk.next_review_at
                            else None
                        ),
                    },
                )
                notif_repo.save(notif)

                # Record in history to prevent duplicate alerts
                history_entry = RiskHistory.create(
                    risk_id=risk.id,
                    event_type=RiskHistoryEventType.REVIEW_COMPLETED,
                    description="Review overdue alert sent",
                    actor_id="system",
                    metadata={
                        "review_overdue_alert": True,
                        "next_review_at": (
                            risk.next_review_at.isoformat()
                            if risk.next_review_at
                            else None
                        ),
                    },
                )
                risk_repo.add_history(history_entry)
                sent += 1

        session.commit()
        logger.info("Sent %d risk review overdue alerts", sent)
        return sent
    except Exception:
        session.rollback()
        logger.exception("Risk review overdue task failed")
        raise
    finally:
        session.close()
