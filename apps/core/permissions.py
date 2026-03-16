from rest_framework.permissions import BasePermission

from apps.core.exceptions import (
    AuthEmailNotVerifiedException,
    AuthTokenMissingException,
    OrgContextRequiredException,
)


class IsAuthenticatedAndVerified(BasePermission):
    """Requires valid JWT bearer + email verified."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            raise AuthTokenMissingException()
        if not request.user.is_email_verified:
            raise AuthEmailNotVerifiedException()
        return True


class HasOrganizationContext(IsAuthenticatedAndVerified):
    """Requires X-Organization-ID header in addition to auth."""

    def has_permission(self, request, view) -> bool:
        super().has_permission(request, view)
        org_id = request.headers.get("X-Organization-ID")
        if not org_id:
            raise OrgContextRequiredException()
        return True

