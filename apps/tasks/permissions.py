from rest_framework.permissions import BasePermission

from apps.projects.models import ProjectMember
from apps.tasks.models import Task


class CanEditTask(BasePermission):
    """User can edit task if they are project manager or task creator/assignee."""
    def has_permission(self, request, view):
        task_id = view.kwargs.get('task_id')
        if not task_id:
            return True
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return False
        
        is_manager = ProjectMember.objects.filter(
            user=request.user,
            project=task.project,
            project_role=ProjectMember.ROLE_MANAGER
        ).exists()
        
        is_creator = task.created_by_user == request.user
        is_assignee = task.assignee_user == request.user
        
        return is_manager or is_creator or is_assignee


class CanDeleteTask(BasePermission):
    """User can delete if they are project manager or task creator."""
    def has_permission(self, request, view):
        task_id = view.kwargs.get('task_id')
        if not task_id:
            return True
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return False
        
        is_manager = ProjectMember.objects.filter(
            user=request.user,
            project=task.project,
            project_role=ProjectMember.ROLE_MANAGER
        ).exists()
        
        is_creator = task.created_by_user == request.user
        
        return is_manager or is_creator

