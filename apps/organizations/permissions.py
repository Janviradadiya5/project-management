from rest_framework.permissions import BasePermission

from apps.organizations.models import OrganizationMembership
from apps.users.models import Role


class IsOrgMember(BasePermission):
    """User must be a member of the organization."""
    def has_permission(self, request, view):
        org_id = view.kwargs.get('organization_id')
        if not org_id:
            return True
        return OrganizationMembership.objects.filter(
            user=request.user,
            organization_id=org_id,
            status=OrganizationMembership.STATUS_ACTIVE
        ).exists()


class IsOrgAdmin(BasePermission):
    """User must be an org admin."""
    def has_permission(self, request, view):
        org_id = view.kwargs.get('organization_id')
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

