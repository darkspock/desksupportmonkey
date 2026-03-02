from unittest.mock import MagicMock, patch

from src.notification_bc.notification.application.services.email_subscriber import (
    EmailSubscriber,
)
from src.notification_bc.notification.domain.enums import EventType
from src.notification_bc.notification.domain.events import DomainEvent

# Patch targets: deferred imports resolve from these modules
_USER_REPO_PATH = "src.auth_bc.user.infrastructure.repository.UserRepository"
_DELAY_PATH = "core.tasks.email_notifications.send_request_notification_email.delay"


def _make_user(user_id: str, email: str, name: str = ""):
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.name = name or email
    return user


def _make_comment_event(
    actor_id="tech1",
    created_by="emp1",
    assigned_to="tech1",
    comment_body="Hello, please check this",
    title="Broken laptop",
):
    return DomainEvent(
        event_type=EventType.REQUEST_COMMENT_ADDED,
        company_id="comp1",
        actor_id=actor_id,
        payload={
            "request_id": "req1",
            "created_by": created_by,
            "assigned_to": assigned_to,
            "title": title,
            "comment_body": comment_body,
        },
        title="New comment",
        body=f"Comment on: {title}",
    )


def _make_status_event(
    actor_id="tech1",
    created_by="emp1",
    assigned_to="tech1",
    new_status="waiting_for_employee",
    title="Broken laptop",
):
    return DomainEvent(
        event_type=EventType.REQUEST_STATUS_CHANGED,
        company_id="comp1",
        actor_id=actor_id,
        payload={
            "request_id": "req1",
            "created_by": created_by,
            "assigned_to": assigned_to,
            "old_status": "in_progress",
            "new_status": new_status,
            "title": title,
        },
        title="Request updated",
        body=f"Status changed from in_progress to {new_status}",
    )


class TestEmailSubscriberCommentRouting:
    """Tests for _handle_comment: routing tech->employee and employee->tech."""

    def test_technician_comment_emails_employee(self):
        """Technician comments -> email sent to employee (created_by)."""
        subscriber = EmailSubscriber()
        db = MagicMock()
        event = _make_comment_event(actor_id="tech1", created_by="emp1", assigned_to="tech1")

        tech_user = _make_user("tech1", "tech@co.com", "Tech One")
        emp_user = _make_user("emp1", "emp@co.com", "Emp One")

        with patch(_USER_REPO_PATH) as MockRepo:
            repo_instance = MockRepo.return_value
            repo_instance.find_by_id.side_effect = lambda uid: {
                "tech1": tech_user, "emp1": emp_user,
            }.get(uid)

            with patch(_DELAY_PATH) as mock_delay:
                subscriber(event, db)

                mock_delay.assert_called_once()
                call_kwargs = mock_delay.call_args[1]
                assert call_kwargs["to_email"] == "emp@co.com"
                assert call_kwargs["to_name"] == "Emp One"
                assert call_kwargs["actor_name"] == "Tech One"
                assert call_kwargs["variant"] == "comment"
                assert call_kwargs["comment_body"] == "Hello, please check this"

    def test_employee_comment_emails_technician(self):
        """Employee comments -> email sent to technician (assigned_to)."""
        subscriber = EmailSubscriber()
        db = MagicMock()
        event = _make_comment_event(actor_id="emp1", created_by="emp1", assigned_to="tech1")

        emp_user = _make_user("emp1", "emp@co.com", "Emp One")
        tech_user = _make_user("tech1", "tech@co.com", "Tech One")

        with patch(_USER_REPO_PATH) as MockRepo:
            repo_instance = MockRepo.return_value
            repo_instance.find_by_id.side_effect = lambda uid: {
                "emp1": emp_user, "tech1": tech_user,
            }.get(uid)

            with patch(_DELAY_PATH) as mock_delay:
                subscriber(event, db)

                mock_delay.assert_called_once()
                call_kwargs = mock_delay.call_args[1]
                assert call_kwargs["to_email"] == "tech@co.com"
                assert call_kwargs["variant"] == "comment"

    def test_employee_comment_no_technician_no_email(self):
        """Employee comments but no assigned technician -> no email."""
        subscriber = EmailSubscriber()
        db = MagicMock()
        event = _make_comment_event(actor_id="emp1", created_by="emp1", assigned_to=None)

        emp_user = _make_user("emp1", "emp@co.com", "Emp One")

        with patch(_USER_REPO_PATH) as MockRepo:
            repo_instance = MockRepo.return_value
            repo_instance.find_by_id.side_effect = lambda uid: {
                "emp1": emp_user,
            }.get(uid)

            with patch(_DELAY_PATH) as mock_delay:
                subscriber(event, db)
                mock_delay.assert_not_called()

    def test_actor_is_only_participant_no_email(self):
        """Actor == created_by with no assigned_to -> no email (nobody to send to)."""
        subscriber = EmailSubscriber()
        db = MagicMock()
        event = _make_comment_event(actor_id="emp1", created_by="emp1", assigned_to=None)

        emp_user = _make_user("emp1", "emp@co.com", "Emp One")

        with patch(_USER_REPO_PATH) as MockRepo:
            repo_instance = MockRepo.return_value
            repo_instance.find_by_id.side_effect = lambda uid: {
                "emp1": emp_user,
            }.get(uid)

            with patch(_DELAY_PATH) as mock_delay:
                subscriber(event, db)
                mock_delay.assert_not_called()

    def test_recipient_no_email_address_no_email(self):
        """Recipient exists but has no email address -> no email."""
        subscriber = EmailSubscriber()
        db = MagicMock()
        event = _make_comment_event(actor_id="tech1", created_by="emp1", assigned_to="tech1")

        tech_user = _make_user("tech1", "tech@co.com", "Tech One")
        emp_user = MagicMock()
        emp_user.id = "emp1"
        emp_user.email = ""  # no email
        emp_user.name = "Emp One"

        with patch(_USER_REPO_PATH) as MockRepo:
            repo_instance = MockRepo.return_value
            repo_instance.find_by_id.side_effect = lambda uid: {
                "tech1": tech_user, "emp1": emp_user,
            }.get(uid)

            with patch(_DELAY_PATH) as mock_delay:
                subscriber(event, db)
                mock_delay.assert_not_called()

    def test_missing_created_by_and_assigned_to_no_email(self):
        """Event payload missing both created_by and assigned_to -> no email."""
        subscriber = EmailSubscriber()
        db = MagicMock()
        event = _make_comment_event(actor_id="tech1", created_by=None, assigned_to=None)

        with patch(_USER_REPO_PATH):
            with patch(_DELAY_PATH) as mock_delay:
                subscriber(event, db)
                mock_delay.assert_not_called()


class TestEmailSubscriberStatusChangeRouting:
    """Tests for _handle_status_change: waiting_for_employee -> email employee."""

    def test_waiting_status_emails_employee(self):
        """Status changes to waiting_for_employee -> email employee."""
        subscriber = EmailSubscriber()
        db = MagicMock()
        event = _make_status_event(
            actor_id="tech1", created_by="emp1", new_status="waiting_for_employee",
        )

        tech_user = _make_user("tech1", "tech@co.com", "Tech One")
        emp_user = _make_user("emp1", "emp@co.com", "Emp One")

        with patch(_USER_REPO_PATH) as MockRepo:
            repo_instance = MockRepo.return_value
            repo_instance.find_by_id.side_effect = lambda uid: {
                "tech1": tech_user, "emp1": emp_user,
            }.get(uid)

            with patch(_DELAY_PATH) as mock_delay:
                subscriber(event, db)

                mock_delay.assert_called_once()
                call_kwargs = mock_delay.call_args[1]
                assert call_kwargs["to_email"] == "emp@co.com"
                assert call_kwargs["variant"] == "action_required"
                assert call_kwargs["request_title"] == "Broken laptop"

    def test_resolved_status_no_email(self):
        """Status changes to resolved -> no email."""
        subscriber = EmailSubscriber()
        db = MagicMock()
        event = _make_status_event(new_status="resolved")

        with patch(_USER_REPO_PATH):
            with patch(_DELAY_PATH) as mock_delay:
                subscriber(event, db)
                mock_delay.assert_not_called()

    def test_waiting_status_self_set_no_email(self):
        """Actor is the employee who set waiting_for_employee on themselves -> no email."""
        subscriber = EmailSubscriber()
        db = MagicMock()
        event = _make_status_event(
            actor_id="emp1", created_by="emp1", new_status="waiting_for_employee",
        )

        with patch(_USER_REPO_PATH):
            with patch(_DELAY_PATH) as mock_delay:
                subscriber(event, db)
                mock_delay.assert_not_called()


class TestEmailSubscriberIgnoresOtherEvents:
    """Subscriber ignores events it doesn't handle."""

    def test_ignores_request_created(self):
        event = DomainEvent(
            event_type=EventType.REQUEST_CREATED,
            company_id="comp1",
            actor_id="user1",
            payload={"request_id": "req1"},
            title="New request",
            body="Created",
        )
        subscriber = EmailSubscriber()
        db = MagicMock()

        with patch(_DELAY_PATH) as mock_delay:
            subscriber(event, db)
            mock_delay.assert_not_called()


class TestCeleryTaskSubjectLines:
    """Test subject line formatting in the Celery task."""

    @patch("core.tasks.email_notifications.get_email_service")
    @patch("core.tasks.email_notifications._jinja_env")
    def test_comment_variant_subject(self, mock_env, mock_get_svc):
        from core.tasks.email_notifications import send_request_notification_email

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>test</html>"
        mock_env.get_template.return_value = mock_template

        mock_svc = MagicMock()
        mock_get_svc.return_value = mock_svc

        send_request_notification_email(
            to_email="emp@co.com",
            to_name="Emp",
            actor_name="Tech",
            request_id="req1",
            request_title="Broken laptop",
            comment_body="Check this",
            variant="comment",
        )

        mock_svc.send.assert_called_once()
        subject = mock_svc.send.call_args[0][1]
        assert "New message on:" in subject
        assert "Broken laptop" in subject

    @patch("core.tasks.email_notifications.get_email_service")
    @patch("core.tasks.email_notifications._jinja_env")
    def test_action_required_variant_subject(self, mock_env, mock_get_svc):
        from core.tasks.email_notifications import send_request_notification_email

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>test</html>"
        mock_env.get_template.return_value = mock_template

        mock_svc = MagicMock()
        mock_get_svc.return_value = mock_svc

        send_request_notification_email(
            to_email="emp@co.com",
            to_name="Emp",
            actor_name="Tech",
            request_id="req1",
            request_title="Broken laptop",
            comment_body="",
            variant="action_required",
        )

        mock_svc.send.assert_called_once()
        subject = mock_svc.send.call_args[0][1]
        assert "Action required:" in subject
        assert "Broken laptop" in subject

    @patch("core.tasks.email_notifications.get_email_service")
    @patch("core.tasks.email_notifications._jinja_env")
    def test_template_renders_with_variables(self, mock_env, mock_get_svc):
        from core.tasks.email_notifications import send_request_notification_email

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>rendered</html>"
        mock_env.get_template.return_value = mock_template

        mock_svc = MagicMock()
        mock_get_svc.return_value = mock_svc

        send_request_notification_email(
            to_email="emp@co.com",
            to_name="Emp",
            actor_name="Tech",
            request_id="req1",
            request_title="Broken laptop",
            comment_body="Please check",
            variant="comment",
        )

        mock_env.get_template.assert_called_once_with("request_comment.html")
        render_kwargs = mock_template.render.call_args[1]
        assert render_kwargs["to_name"] == "Emp"
        assert render_kwargs["actor_name"] == "Tech"
        assert render_kwargs["request_title"] == "Broken laptop"
        assert render_kwargs["comment_body"] == "Please check"
        assert "req1" in render_kwargs["request_url"]

    @patch("core.tasks.email_notifications.get_email_service")
    @patch("core.tasks.email_notifications._jinja_env")
    def test_email_service_failure_raises_for_retry(self, mock_env, mock_get_svc):
        from core.tasks.email_notifications import send_request_notification_email

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>test</html>"
        mock_env.get_template.return_value = mock_template

        mock_svc = MagicMock()
        mock_svc.send.side_effect = RuntimeError("Brevo API 500")
        mock_get_svc.return_value = mock_svc

        import pytest
        with pytest.raises(Exception):
            send_request_notification_email(
                to_email="emp@co.com",
                to_name="Emp",
                actor_name="Tech",
                request_id="req1",
                request_title="Broken laptop",
                comment_body="",
                variant="comment",
            )
