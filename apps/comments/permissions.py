from rest_framework.permissions import BasePermission


class CanEditComment(BasePermission):
    """User can edit only their own comments."""
    def has_object_permission(self, request, view, obj):
        return obj.author_user == request.user


class CanDeleteComment(BasePermission):
    """User can delete only their own comments."""
    def has_object_permission(self, request, view, obj):
        return obj.author_user == request.user

