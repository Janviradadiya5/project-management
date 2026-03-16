"""Service-layer business logic for app: comments."""

from apps.comments.models import Comment
from apps.organizations.models import OrganizationMembership
from apps.projects.models import ProjectMember
from apps.tasks.models import Task
from apps.users.models import User


class CommentService:
    WRITE_ROLES = {"organization_admin", "project_manager", "team_member"}
    ADMIN_ROLES = {"organization_admin", "project_manager"}

    @staticmethod
    def is_super_admin(user: User) -> bool:
        return bool(getattr(user, "is_superuser", False))

    @staticmethod
    def role_in_org(user: User, org) -> str | None:
        if CommentService.is_super_admin(user):
            return "super_admin"
        membership = (
            OrganizationMembership.objects.select_related("role")
            .filter(user=user, organization=org, status=OrganizationMembership.STATUS_ACTIVE)
            .first()
        )
        return membership.role.code if membership else None

    @staticmethod
    def can_access_task(user: User, task: Task) -> bool:
        if CommentService.is_super_admin(user):
            return True
        role = CommentService.role_in_org(user, task.project.organization)
        return bool(role)

    @staticmethod
    def can_write_comment(user: User, task: Task) -> bool:
        role = CommentService.role_in_org(user, task.project.organization)
        if role == "super_admin" or role in CommentService.WRITE_ROLES:
            return True
        return False

    @staticmethod
    def can_edit_or_delete_comment(user: User, comment: Comment) -> bool:
        role = CommentService.role_in_org(user, comment.task.project.organization)
        if role == "super_admin" or role in CommentService.ADMIN_ROLES:
            return True
        return comment.author_user_id == user.id

    @staticmethod
    def is_active_project_member(user: User, task: Task) -> bool:
        return ProjectMember.objects.filter(project=task.project, user=user).exists()

