"""Service-layer business logic for app: projects."""

from uuid import UUID

from apps.core.exceptions import OrgAccessDeniedException, OrgNotFoundOrDeletedException, ResourceNotFoundException, TaskAssigneeNotMemberException
from apps.organizations.models import Organization, OrganizationMembership
from apps.projects.models import Project, ProjectMember
from apps.users.models import User



class ProjectService:
    READ_ROLES = {"organization_admin", "project_manager", "team_member", "viewer"}
    WRITE_ROLES = {"organization_admin", "project_manager"}
    ADMIN_ROLES = {"organization_admin"}

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
    def role_in_org(user: User, org: Organization) -> str | None:
        if ProjectService.is_super_admin(user):
            return "super_admin"
        membership = (
            OrganizationMembership.objects.select_related("role")
            .filter(user=user, organization=org, status=OrganizationMembership.STATUS_ACTIVE)
            .first()
        )
        return membership.role.code if membership else None

    @staticmethod
    def require_org_role(user: User, org: Organization, allowed_roles: set[str]) -> str:
        role = ProjectService.role_in_org(user, org)
        if role == "super_admin" or role in allowed_roles:
            return role or "super_admin"
        raise OrgAccessDeniedException(
            "You do not have access to this organization.",
            extra_details={"organization_id": str(org.id)},
        )

    @staticmethod
    def get_project_or_404(project_id: str, org: Organization) -> Project:
        try:
            pid = UUID(str(project_id))
        except ValueError as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"id": ["Must be a valid UUID."]}) from exc
        try:
            return Project.objects.get(id=pid, organization=org, deleted_at__isnull=True)
        except Project.DoesNotExist as exc:
            raise OrgNotFoundOrDeletedException(
                "Organization not found or has been deleted.",
                extra_details={"project_id": str(project_id), "organization_id": str(org.id)},
            ) from exc

    @staticmethod
    def can_edit_project(user: User, project: Project) -> bool:
        """Check if user can edit project."""
        is_manager = ProjectMember.objects.filter(
            user=user,
            project=project,
            project_role=ProjectMember.ROLE_MANAGER,
        ).exists()
        is_creator = project.created_by_user == user
        is_org_admin = OrganizationMembership.objects.filter(
            user=user,
            organization=project.organization,
            role__code="organization_admin",
            status=OrganizationMembership.STATUS_ACTIVE,
        ).exists()
        return is_manager or is_creator or is_org_admin

    @staticmethod
    def can_delete_project(user: User, project: Project) -> bool:
        """Check if user can delete project."""
        is_manager = ProjectMember.objects.filter(
            user=user,
            project=project,
            project_role=ProjectMember.ROLE_MANAGER,
        ).exists()
        is_org_admin = OrganizationMembership.objects.filter(
            user=user,
            organization=project.organization,
            role__code="organization_admin",
            status=OrganizationMembership.STATUS_ACTIVE,
        ).exists()
        return is_manager or is_org_admin

    @staticmethod
    def can_manage_members(user: User, project: Project) -> bool:
        """Check if user can manage project members."""
        is_manager = ProjectMember.objects.filter(
            user=user,
            project=project,
            project_role=ProjectMember.ROLE_MANAGER,
        ).exists()
        is_org_admin = OrganizationMembership.objects.filter(
            user=user,
            organization=project.organization,
            role__code="organization_admin",
            status=OrganizationMembership.STATUS_ACTIVE,
        ).exists()
        return is_manager or is_org_admin

    @staticmethod
    def add_member(project: Project, user_id, role_code: str, added_by: User) -> None:
        """Add member to project."""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ResourceNotFoundException()
        
        is_org_member = OrganizationMembership.objects.filter(
            user=user,
            organization=project.organization,
            status=OrganizationMembership.STATUS_ACTIVE,
        ).exists()
        if not is_org_member:
            raise ValueError("User is not an active organization member.")
        
        ProjectMember.objects.get_or_create(
            project=project,
            user=user,
            defaults={
                "project_role": role_code,
                "added_by_user": added_by,
            },
        )

    @staticmethod
    def add_member_strict(project: Project, user_id, role_code: str, added_by: User) -> ProjectMember:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise ResourceNotFoundException(
                "User not found.",
                extra_details={"user_id": str(user_id)},
            ) from exc

        is_org_member = OrganizationMembership.objects.filter(
            user=user,
            organization=project.organization,
            status=OrganizationMembership.STATUS_ACTIVE,
        ).exists()
        if not is_org_member:
            raise TaskAssigneeNotMemberException(
                "The specified user is not an active organization member and cannot be added to the project.",
                extra_details={"user_id": str(user_id), "project_id": str(project.id)},
            )

        existing = ProjectMember.objects.filter(project=project, user=user).first()
        if existing:
            from apps.core.exceptions import ResourceConflictException

            raise ResourceConflictException(
                "User is already a member of this project.",
                extra_details={"user_id": str(user_id), "project_id": str(project.id)},
            )

        return ProjectMember.objects.create(
            project=project,
            user=user,
            project_role=role_code,
            added_by_user=added_by,
        )

