"""Service-layer business logic for app: attachments."""

from uuid import UUID

from apps.attachments.models import Attachment
from apps.core.exceptions import AttachmentAccessForbiddenException, OrgAccessDeniedException, ResourceNotFoundException
from apps.organizations.models import OrganizationMembership
from apps.tasks.models import Task
from apps.users.models import User


class AttachmentService:
    READ_ROLES = {"organization_admin", "project_manager", "team_member", "viewer"}
    WRITE_ROLES = {"organization_admin", "project_manager", "team_member"}

    @staticmethod
    def is_super_admin(user: User) -> bool:
        return bool(getattr(user, "is_superuser", False))

    @staticmethod
    def role_in_org(user: User, org) -> str | None:
        if AttachmentService.is_super_admin(user):
            return "super_admin"
        membership = (
            OrganizationMembership.objects.select_related("role")
            .filter(user=user, organization=org, status=OrganizationMembership.STATUS_ACTIVE)
            .first()
        )
        return membership.role.code if membership else None

    @staticmethod
    def require_org_role(user: User, org, allowed_roles: set[str]) -> str:
        role = AttachmentService.role_in_org(user, org)
        if role == "super_admin" or role in allowed_roles:
            return role or "super_admin"
        raise OrgAccessDeniedException(
            "You do not have access to this organization.",
            extra_details={"organization_id": str(org.id)},
        )

    @staticmethod
    def get_task_or_404(task_id: str, org):
        try:
            tid = UUID(str(task_id))
        except ValueError as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"task_id": ["Must be a valid UUID."]}) from exc
        try:
            return Task.objects.select_related("project", "project__organization").get(
                id=tid,
                project__organization=org,
                deleted_at__isnull=True,
            )
        except Task.DoesNotExist as exc:
            from apps.core.exceptions import OrgNotFoundOrDeletedException

            raise OrgNotFoundOrDeletedException(
                "Organization/task not found or deleted.",
                extra_details={"task_id": str(task_id), "organization_id": str(org.id)},
            ) from exc

    @staticmethod
    def get_attachment_or_404(attachment_id: str, org):
        try:
            aid = UUID(str(attachment_id))
        except ValueError as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"id": ["Must be a valid UUID."]}) from exc
        try:
            return Attachment.objects.select_related("task", "task__project").get(
                id=aid,
                task__project__organization=org,
            )
        except Attachment.DoesNotExist as exc:
            from apps.core.exceptions import OrgNotFoundOrDeletedException

            raise OrgNotFoundOrDeletedException(
                "Organization/attachment not found or deleted.",
                extra_details={"attachment_id": str(attachment_id), "organization_id": str(org.id)},
            ) from exc

    @staticmethod
    def ensure_can_view(user: User, task: Task):
        AttachmentService.require_org_role(user, task.project.organization, AttachmentService.READ_ROLES)

    @staticmethod
    def ensure_can_upload(user: User, task: Task):
        AttachmentService.require_org_role(user, task.project.organization, AttachmentService.WRITE_ROLES)

    @staticmethod
    def ensure_can_delete(user: User, attachment: Attachment):
        role = AttachmentService.role_in_org(user, attachment.task.project.organization)
        if role == "super_admin" or role in {"organization_admin", "project_manager"}:
            return
        if role == "team_member" and attachment.uploaded_by_user_id == user.id:
            return
        raise AttachmentAccessForbiddenException(
            "You do not have permission to delete attachment.",
            extra_details={"attachment_id": str(attachment.id)},
        )

