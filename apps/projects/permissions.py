from rest_framework.permissions import BasePermission

from apps.projects.models import ProjectMember


class IsProjectMember(BasePermission):
    """User must be a member of the project."""
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return True
        return ProjectMember.objects.filter(
            user=request.user,
            project_id=project_id
        ).exists()


class IsProjectManager(BasePermission):
    """User must be a project manager."""
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return False
        return ProjectMember.objects.filter(
            user=request.user,
            project_id=project_id,
            project_role=ProjectMember.ROLE_MANAGER
        ).exists()

