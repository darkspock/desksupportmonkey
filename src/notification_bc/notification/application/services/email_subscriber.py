import logging

from sqlalchemy.orm import Session

from src.notification_bc.notification.domain.enums import EventType
from src.notification_bc.notification.domain.events import DomainEvent

logger = logging.getLogger(__name__)


class EmailSubscriber:
    """EventBus subscriber that queues email notifications via Celery.

    Listens for:
    - REQUEST_COMMENT_ADDED -> email the "other side" (tech->employee or employee->tech)
    - REQUEST_STATUS_CHANGED where new_status == "waiting_for_employee" -> email employee
    """

    def __call__(self, event: DomainEvent, db: Session) -> None:
        if event.event_type == EventType.REQUEST_COMMENT_ADDED:
            self._handle_comment(event, db)
        elif event.event_type == EventType.REQUEST_STATUS_CHANGED:
            self._handle_status_change(event, db)

    def _handle_comment(self, event: DomainEvent, db: Session) -> None:
        """Route: technician comment -> email employee; employee comment -> email technician."""
        from src.auth_bc.user.infrastructure.repository import UserRepository

        actor_id = event.actor_id
        created_by = event.payload.get("created_by")
        assigned_to = event.payload.get("assigned_to")

        if not created_by and not assigned_to:
            return

        user_repo = UserRepository(db)
        actor = user_repo.find_by_id(actor_id)
        if not actor:
            return

        # Determine recipient: if actor is the employee (created_by), email technician;
        # otherwise email employee
        if actor_id == created_by:
            # Employee commented -> email assigned technician
            if not assigned_to:
                return  # No technician assigned — skip email (in-app only)
            recipient = user_repo.find_by_id(assigned_to)
        else:
            # Technician/other commented -> email the employee (created_by)
            recipient = user_repo.find_by_id(created_by) if created_by else None

        if not recipient or not recipient.email:
            return

        self._enqueue_email(
            to_email=recipient.email,
            to_name=recipient.name or recipient.email,
            actor_name=actor.name or actor.email,
            request_id=event.payload.get("request_id", ""),
            request_title=event.payload.get("title", ""),
            comment_body=event.payload.get("comment_body", ""),
            variant="comment",
        )

    def _handle_status_change(self, event: DomainEvent, db: Session) -> None:
        """Send 'action required' email to employee when status -> waiting_for_employee."""
        new_status = event.payload.get("new_status")
        if new_status != "waiting_for_employee":
            return

        created_by = event.payload.get("created_by")
        if not created_by:
            return

        # Don't email the actor if they set the status themselves
        if event.actor_id == created_by:
            return

        from src.auth_bc.user.infrastructure.repository import UserRepository

        user_repo = UserRepository(db)
        actor = user_repo.find_by_id(event.actor_id)
        recipient = user_repo.find_by_id(created_by)

        if not recipient or not recipient.email:
            return

        self._enqueue_email(
            to_email=recipient.email,
            to_name=recipient.name or recipient.email,
            actor_name=actor.name or actor.email if actor else "Technician",
            request_id=event.payload.get("request_id", ""),
            request_title=event.payload.get("title", ""),
            comment_body="",
            variant="action_required",
        )

    def _enqueue_email(
        self,
        to_email: str,
        to_name: str,
        actor_name: str,
        request_id: str,
        request_title: str,
        comment_body: str,
        variant: str,
    ) -> None:
        from core.tasks.email_notifications import send_request_notification_email

        send_request_notification_email.delay(
            to_email=to_email,
            to_name=to_name,
            actor_name=actor_name,
            request_id=request_id,
            request_title=request_title,
            comment_body=comment_body,
            variant=variant,
        )
