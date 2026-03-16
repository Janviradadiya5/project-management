from rest_framework.permissions import BasePermission

from apps.organizations.models import OrganizationMembership
from apps.users.models import Role


class CanViewActivityLogs(BasePermission):
    """Only org admins and super admins can view activity logs."""
    def has_permission(self, request, view):
        org_id = request.headers.get('X-Organization-ID')
        if not org_id:
            return False
        try:
            admin_role = Role.objects.get(code='organization_admin')
        except Role.DoesNotExist:
            return False
        return OrganizationMembership.objects.filter(
            user=request.user,
            organization_id=org_id,
            role=admin_role,
            status=OrganizationMembership.STATUS_ACTIVE
        ).exists()

