"""Tests for Notification model."""

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.notifications.models import Notification


@pytest.mark.django_db
class TestNotificationModel:
    """Test cases for Notification model."""

    def test_create_notification_with_valid_data(self, organization, authenticated_user):
        """Test creating a notification with valid data."""
        notification = Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="task_created",
            title="New Task",
            body="A new task has been assigned to you.",
        )
        assert notification.id is not None
        assert notification.recipient_user == authenticated_user
        assert notification.organization == organization
        assert notification.type == "task_created"
        assert notification.is_read is False
        assert notification.read_at is None
        assert notification.created_at is not None

    def test_notification_string_representation(self, organization, authenticated_user):
        """Test __str__ method."""
        notification = Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="project_update",
            title="Project Updated",
            body="Project details have been updated.",
        )
        str_repr = str(notification)
        assert "Notification" in str_repr
        assert "project_update" in str_repr

    def test_notification_with_payload(self, organization, authenticated_user):
        """Test creating notification with JSON payload."""
        payload = {
            "task_id": "uuid-123",
            "task_title": "Important Task",
            "priority": "high",
        }
        notification = Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="task_assigned",
            title="Task Assigned",
            body="You have been assigned a task.",
            payload_json=payload,
        )
        notification.refresh_from_db()
        assert notification.payload_json == payload
        assert notification.payload_json["task_id"] == "uuid-123"

    def test_notification_mark_as_read(self, organization, authenticated_user):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="notification",
            title="Title",
            body="Body",
        )
        assert notification.is_read is False
        assert notification.read_at is None
        
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        notification.refresh_from_db()
        assert notification.is_read is True
        assert notification.read_at is not None

    def test_notification_clean_read_at_requires_is_read(self, organization, authenticated_user):
        """Test that read_at requires is_read=True."""
        notification = Notification(
            recipient_user=authenticated_user,
            organization=organization,
            type="test",
            title="Test",
            body="Test",
            is_read=False,
            read_at=timezone.now(),
        )
        with pytest.raises(ValidationError):
            notification.clean()

    def test_notification_created_at_auto_generated(self, organization, authenticated_user):
        """Test that created_at is automatically set."""
        before = timezone.now()
        notification = Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="event",
            title="Event",
            body="An event occurred.",
        )
        after = timezone.now()
        assert before <= notification.created_at <= after

    def test_notification_default_payload(self, organization, authenticated_user):
        """Test that default payload is empty dict."""
        notification = Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="simple",
            title="Simple",
            body="No payload",
        )
        assert notification.payload_json == {}

    def test_notification_foreign_key_cascade_user(self, notification):
        """Test that deleting user cascades to notifications."""
        notification_id = notification.id
        user = notification.recipient_user
        user.delete()
        assert not Notification.objects.filter(id=notification_id).exists()

    def test_notification_foreign_key_cascade_org(self, notification):
        """Test that deleting org cascades to notifications."""
        notification_id = notification.id
        org = notification.organization
        org.delete()
        assert not Notification.objects.filter(id=notification_id).exists()

    def test_multiple_notifications_per_user(self, organization, authenticated_user):
        """Test multiple notifications for same user."""
        for i in range(5):
            Notification.objects.create(
                recipient_user=authenticated_user,
                organization=organization,
                type=f"type{i}",
                title=f"Notification {i}",
                body=f"Body {i}",
            )
        assert authenticated_user.notifications.count() == 5

    def test_notification_types_variety(self, organization, authenticated_user):
        """Test various notification types."""
        types = [
            "task_created",
            "task_assigned",
            "comment_added",
            "attachment_uploaded",
            "project_updated",
        ]
        for n_type in types:
            notification = Notification.objects.create(
                recipient_user=authenticated_user,
                organization=organization,
                type=n_type,
                title=f"{n_type}",
                body="Test body",
            )
            assert notification.type == n_type

