from rest_framework.permissions import BasePermission


class IsNotificationRecipient(BasePermission):
    """User can only access their own notifications."""
    def has_object_permission(self, request, view, obj):
        return obj.recipient_user == request.user

