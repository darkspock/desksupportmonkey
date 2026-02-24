import logging
from datetime import datetime, timezone

from sqlalchemy import select, text

from core.celery import celery_app

logger = logging.getLogger(__name__)

# Priority escalation order (lower index = higher priority)
PRIORITY_ESCALATION = {"low": "medium", "medium": "high", "high": "urgent"}


@celery_app.task(name="core.tasks.sla.check_sla_breaches")
def check_sla_breaches() -> int:
    """Detect SLA breaches for open requests across all companies."""
    from core.database import SessionLocal
    from src.notification_bc.notification.domain.enums import EventType
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )
    from src.auth_bc.user.infrastructure.repository import UserRepository
    from src.sla_bc.sla.domain.entities import SlaBreachRecord
    from src.sla_bc.sla.domain.enums import SlaBreachType
    from src.sla_bc.sla.infrastructure.models import SlaPolicyModel
    from src.sla_bc.sla.infrastructure.repository import SlaRepository

    session = SessionLocal()
    breaches_recorded = 0
    try:
        sla_repo = SlaRepository(session)
        notif_repo = NotificationRepository(session)
        user_repo = UserRepository(session)

        # Get distinct companies with active SLA policies
        company_ids = (
            session.execute(
                select(SlaPolicyModel.company_id).where(
                    SlaPolicyModel.is_active.is_(True)
                ).distinct()
            )
            .scalars()
            .all()
        )

        now = datetime.now(timezone.utc)

        for company_id in company_ids:
            # Cache admin IDs per company for breach notifications
            admin_ids = user_repo.find_admin_ids_by_company(company_id)

            # Get open requests for this company
            rows = session.execute(
                text(
                    """
                    SELECT id, type, priority, status, assigned_to,
                           created_at, first_response_at
                    FROM service_requests
                    WHERE company_id = :cid
                      AND status NOT IN ('resolved', 'rejected')
                    """
                ),
                {"cid": company_id},
            ).fetchall()

            for row in rows:
                req_id = row[0]
                req_type = row[1]
                req_priority = row[2]
                req_assigned_to = row[4]
                req_created_at = row[5]
                req_first_response_at = row[6]

                policy = sla_repo.find_policy_for_request(
                    company_id=company_id,
                    priority=req_priority,
                    request_type=req_type,
                )
                if not policy:
                    continue

                # Calculate elapsed times
                if req_first_response_at:
                    response_hours = (
                        req_first_response_at - req_created_at
                    ).total_seconds() / 3600
                else:
                    response_hours = (
                        now - req_created_at
                    ).total_seconds() / 3600

                resolution_hours = (
                    now - req_created_at
                ).total_seconds() / 3600

                warning_pct = policy.warning_threshold_pct / 100

                # Check response warning
                if (
                    not req_first_response_at
                    and response_hours >= policy.response_time_hours * warning_pct
                    and not sla_repo.has_breach_of_type(
                        req_id, SlaBreachType.RESPONSE_WARNING.value
                    )
                ):
                    breach = SlaBreachRecord.create(
                        company_id=company_id,
                        request_id=req_id,
                        policy_id=policy.id,
                        breach_type=SlaBreachType.RESPONSE_WARNING,
                        target_hours=policy.response_time_hours,
                        actual_hours=round(response_hours, 2),
                    )
                    sla_repo.save_breach(breach)
                    breaches_recorded += 1

                    if req_assigned_to:
                        _send_notification(
                            notif_repo,
                            user_id=req_assigned_to,
                            company_id=company_id,
                            event_type=EventType.SLA_WARNING.value,
                            title="SLA response warning",
                            body=f"Request {req_id} is approaching response time limit",
                            data={
                                "request_id": req_id,
                                "breach_type": "response_warning",
                                "target_hours": policy.response_time_hours,
                                "elapsed_hours": round(response_hours, 2),
                            },
                        )

                # Check response breach
                if (
                    not req_first_response_at
                    and response_hours >= policy.response_time_hours
                    and not sla_repo.has_breach_of_type(
                        req_id, SlaBreachType.RESPONSE_BREACH.value
                    )
                ):
                    breach = SlaBreachRecord.create(
                        company_id=company_id,
                        request_id=req_id,
                        policy_id=policy.id,
                        breach_type=SlaBreachType.RESPONSE_BREACH,
                        target_hours=policy.response_time_hours,
                        actual_hours=round(response_hours, 2),
                        escalated=policy.escalate_on_breach,
                    )
                    sla_repo.save_breach(breach)
                    breaches_recorded += 1

                    # Notify assigned technician
                    if req_assigned_to:
                        _send_notification(
                            notif_repo,
                            user_id=req_assigned_to,
                            company_id=company_id,
                            event_type=EventType.SLA_RESPONSE_BREACHED.value,
                            title="SLA response breached",
                            body=f"Request {req_id} has exceeded response time limit",
                            data={
                                "request_id": req_id,
                                "breach_type": "response_breach",
                                "target_hours": policy.response_time_hours,
                                "elapsed_hours": round(response_hours, 2),
                            },
                        )

                    # Notify admins on breach
                    for admin_id in admin_ids:
                        if admin_id != req_assigned_to:
                            _send_notification(
                                notif_repo,
                                user_id=admin_id,
                                company_id=company_id,
                                event_type=EventType.SLA_RESPONSE_BREACHED.value,
                                title="SLA response breached",
                                body=f"Request {req_id} has exceeded response time limit",
                                data={
                                    "request_id": req_id,
                                    "breach_type": "response_breach",
                                    "target_hours": policy.response_time_hours,
                                    "elapsed_hours": round(response_hours, 2),
                                },
                            )

                    # Auto-escalate priority
                    if policy.escalate_on_breach:
                        _escalate_priority(session, req_id, req_priority)

                # Check resolution warning
                if (
                    resolution_hours >= policy.resolution_time_hours * warning_pct
                    and not sla_repo.has_breach_of_type(
                        req_id, SlaBreachType.RESOLUTION_WARNING.value
                    )
                ):
                    breach = SlaBreachRecord.create(
                        company_id=company_id,
                        request_id=req_id,
                        policy_id=policy.id,
                        breach_type=SlaBreachType.RESOLUTION_WARNING,
                        target_hours=policy.resolution_time_hours,
                        actual_hours=round(resolution_hours, 2),
                    )
                    sla_repo.save_breach(breach)
                    breaches_recorded += 1

                    if req_assigned_to:
                        _send_notification(
                            notif_repo,
                            user_id=req_assigned_to,
                            company_id=company_id,
                            event_type=EventType.SLA_WARNING.value,
                            title="SLA resolution warning",
                            body=f"Request {req_id} is approaching resolution time limit",
                            data={
                                "request_id": req_id,
                                "breach_type": "resolution_warning",
                                "target_hours": policy.resolution_time_hours,
                                "elapsed_hours": round(resolution_hours, 2),
                            },
                        )

                # Check resolution breach
                if (
                    resolution_hours >= policy.resolution_time_hours
                    and not sla_repo.has_breach_of_type(
                        req_id, SlaBreachType.RESOLUTION_BREACH.value
                    )
                ):
                    breach = SlaBreachRecord.create(
                        company_id=company_id,
                        request_id=req_id,
                        policy_id=policy.id,
                        breach_type=SlaBreachType.RESOLUTION_BREACH,
                        target_hours=policy.resolution_time_hours,
                        actual_hours=round(resolution_hours, 2),
                        escalated=policy.escalate_on_breach,
                    )
                    sla_repo.save_breach(breach)
                    breaches_recorded += 1

                    # Notify assigned technician
                    if req_assigned_to:
                        _send_notification(
                            notif_repo,
                            user_id=req_assigned_to,
                            company_id=company_id,
                            event_type=EventType.SLA_RESOLUTION_BREACHED.value,
                            title="SLA resolution breached",
                            body=f"Request {req_id} has exceeded resolution time limit",
                            data={
                                "request_id": req_id,
                                "breach_type": "resolution_breach",
                                "target_hours": policy.resolution_time_hours,
                                "elapsed_hours": round(resolution_hours, 2),
                            },
                        )

                    # Notify admins on breach
                    for admin_id in admin_ids:
                        if admin_id != req_assigned_to:
                            _send_notification(
                                notif_repo,
                                user_id=admin_id,
                                company_id=company_id,
                                event_type=EventType.SLA_RESOLUTION_BREACHED.value,
                                title="SLA resolution breached",
                                body=f"Request {req_id} has exceeded resolution time limit",
                                data={
                                    "request_id": req_id,
                                    "breach_type": "resolution_breach",
                                    "target_hours": policy.resolution_time_hours,
                                    "elapsed_hours": round(resolution_hours, 2),
                                },
                            )

                    # Auto-escalate priority
                    if policy.escalate_on_breach:
                        _escalate_priority(session, req_id, req_priority)

        session.commit()
        logger.info("SLA breach check: %d new breaches recorded", breaches_recorded)
        return breaches_recorded
    except Exception:
        session.rollback()
        logger.exception("SLA breach check task failed")
        raise
    finally:
        session.close()


def _send_notification(
    notif_repo,
    user_id: str,
    company_id: str,
    event_type: str,
    title: str,
    body: str,
    data: dict,
) -> None:
    from src.notification_bc.notification.domain.entities import Notification

    notif = Notification.create(
        user_id=user_id,
        company_id=company_id,
        event_type=event_type,
        title=title,
        body=body,
        data=data,
    )
    notif_repo.save(notif)


def _escalate_priority(session, request_id: str, current_priority: str) -> None:
    """Bump request priority one level up if not already urgent."""
    new_priority = PRIORITY_ESCALATION.get(current_priority)
    if not new_priority:
        return  # Already urgent or unknown

    session.execute(
        text(
            "UPDATE service_requests SET priority = :new_prio WHERE id = :rid"
        ),
        {"new_prio": new_priority, "rid": request_id},
    )
    logger.info(
        "SLA auto-escalation: request %s priority %s -> %s",
        request_id,
        current_priority,
        new_priority,
    )
