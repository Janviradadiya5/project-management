from rest_framework.permissions import BasePermission


class CanDeleteAttachment(BasePermission):
    """User can delete only their own attachments."""
    def has_object_permission(self, request, view, obj):
        return obj.uploaded_by_user == request.user

