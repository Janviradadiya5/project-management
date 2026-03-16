"""Tests for Notification service business logic."""

import pytest

from apps.notifications.services import NotificationService


@pytest.mark.django_db
class TestNotificationService:
    """Test cases for NotificationService methods."""

    def test_create_notification_success(self, organization, authenticated_user):
        """Test successfully creating a notification."""
        notification = NotificationService.create_notification(
            recipient_user=authenticated_user,
            organization=organization,
            notification_type="task_assigned",
            title="New Task",
            body="You have been assigned a task.",
        )
        assert notification.id is not None
        assert notification.recipient_user == authenticated_user
        assert notification.organization == organization
        assert notification.type == "task_assigned"
        assert notification.payload_json == {}

    def test_create_notification_with_payload(self, organization, authenticated_user):
        """Test creating notification with payload."""
        payload = {"task_id": "123", "priority": "high"}
        notification = NotificationService.create_notification(
            recipient_user=authenticated_user,
            organization=organization,
            notification_type="task_created",
            title="Task Created",
            body="A new task has been created.",
            payload=payload,
        )
        assert notification.payload_json == payload

    def test_create_notification_payload_optional(self, organization, authenticated_user):
        """Test that payload is optional."""
        notification = NotificationService.create_notification(
            recipient_user=authenticated_user,
            organization=organization,
            notification_type="reminder",
            title="Reminder",
            body="This is a reminder.",
        )
        assert notification.payload_json == {}

    def test_create_notification_persists_to_database(self, organization, authenticated_user):
        """Test that notification is persisted to database."""
        NotificationService.create_notification(
            recipient_user=authenticated_user,
            organization=organization,
            notification_type="test",
            title="Test",
            body="Test body",
        )
        assert authenticated_user.notifications.count() == 1

    def test_create_multiple_notifications(self, organization, authenticated_user):
        """Test creating multiple notifications for same user."""
        for i in range(5):
            NotificationService.create_notification(
                recipient_user=authenticated_user,
                organization=organization,
                notification_type=f"type{i}",
                title=f"Title {i}",
                body=f"Body {i}",
            )
        assert authenticated_user.notifications.count() == 5

