"""Service-layer business logic for app: tasks."""

from uuid import UUID

from apps.core.exceptions import (
    OrgAccessDeniedException,
    OrgNotFoundOrDeletedException,
    ResourceNotFoundException,
    TaskAssigneeNotMemberException,
)
from apps.organizations.models import Organization, OrganizationMembership
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task
from apps.users.models import User


class TaskService:
    READ_ROLES = {"organization_admin", "project_manager", "team_member", "viewer"}
    WRITE_ROLES = {"organization_admin", "project_manager", "team_member"}
    ADMIN_ROLES = {"organization_admin", "project_manager"}

    @staticmethod
    def is_super_admin(user: User) -> bool:
        return bool(getattr(user, "is_superuser", False))

    @staticmethod
    def get_org_or_404(org_id: str) -> Organization:
        try:
            oid = UUID(str(org_id))
        except ValueError as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"X-Organization-ID": ["Must be a valid UUID."]}) from exc
        try:
            org = Organization.objects.get(id=oid)
        except Organization.DoesNotExist as exc:
            raise OrgNotFoundOrDeletedException(
                "Organization not found or has been deleted.",
                extra_details={"organization_id": str(org_id)},
            ) from exc
        if org.deleted_at:
            raise OrgNotFoundOrDeletedException(
                "Organization not found or has been deleted.",
                extra_details={"organization_id": str(org_id)},
            )
        return org

    @staticmethod
    def get_role_code_in_org(user: User, org: Organization) -> str | None:
        if TaskService.is_super_admin(user):
            return "super_admin"
        membership = (
            OrganizationMembership.objects.select_related("role")
            .filter(user=user, organization=org, status=OrganizationMembership.STATUS_ACTIVE)
            .first()
        )
        return membership.role.code if membership else None

    @staticmethod
    def require_role(user: User, org: Organization, allowed_roles: set[str]) -> str:
        role = TaskService.get_role_code_in_org(user, org)
        if role == "super_admin" or role in allowed_roles:
            return role or "super_admin"
        raise OrgAccessDeniedException(
            "You do not have access to this organization.",
            extra_details={"organization_id": str(org.id)},
        )

    @staticmethod
    def get_project_in_org_or_404(project_id: str, org: Organization) -> Project:
        try:
            pid = UUID(str(project_id))
        except ValueError as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"project_id": ["Must be a valid UUID."]}) from exc
        try:
            return Project.objects.get(id=pid, organization=org, deleted_at__isnull=True)
        except Project.DoesNotExist as exc:
            raise OrgNotFoundOrDeletedException(
                "Organization or project not found.",
                extra_details={"project_id": str(project_id), "organization_id": str(org.id)},
            ) from exc

    @staticmethod
    def get_task_in_org_or_404(task_id: str, org: Organization) -> Task:
        try:
            tid = UUID(str(task_id))
        except ValueError as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"id": ["Must be a valid UUID."]}) from exc
        try:
            return Task.objects.select_related("project").get(
                id=tid,
                project__organization=org,
                deleted_at__isnull=True,
            )
        except Task.DoesNotExist as exc:
            raise ResourceNotFoundException(
                "Task not found.",
                extra_details={"task_id": str(task_id)},
            ) from exc

    @staticmethod
    def validate_assignee_membership(project: Project, assignee_user_id: str) -> None:
        is_project_member = ProjectMember.objects.filter(
            project=project,
            user_id=assignee_user_id,
        ).exists()
        is_org_member = OrganizationMembership.objects.filter(
            organization=project.organization,
            user_id=assignee_user_id,
            status=OrganizationMembership.STATUS_ACTIVE,
        ).exists()
        if not is_project_member or not is_org_member:
            raise TaskAssigneeNotMemberException(
                "The selected assignee is not an active member of this project.",
                extra_details={"assignee_user_id": str(assignee_user_id), "project_id": str(project.id)},
            )

