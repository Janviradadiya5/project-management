from rest_framework.permissions import BasePermission


class IsPublicAuth(BasePermission):
    """Public endpoints don't require authentication."""
    pass

