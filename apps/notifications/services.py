"""Service-layer business logic for app: notifications."""

from apps.notifications.models import Notification


class NotificationService:
    @staticmethod
    def create_notification(
        recipient_user,
        organization,
        notification_type: str,
        title: str,
        body: str,
        payload: dict = None,
    ) -> Notification:
        """Create a new notification."""
        return Notification.objects.create(
            recipient_user=recipient_user,
            organization=organization,
            type=notification_type,
            title=title,
            body=body,
            payload_json=payload or {},
        )

