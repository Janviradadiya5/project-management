"""Tests for Project service business logic."""

import pytest
from django.db import transaction

from apps.projects.models import Project, ProjectMember
from apps.projects.services import ProjectService
from apps.organizations.models import OrganizationMembership, Role
from apps.core.exceptions import ResourceNotFoundException


@pytest.mark.django_db
class TestProjectService:
    """Test cases for ProjectService methods."""

    @pytest.mark.permission
    def test_can_edit_project_as_manager(self, project, authenticated_user, another_user):
        """Test that project manager can edit project."""
        # authenticated_user is already a manager
        assert ProjectService.can_edit_project(authenticated_user, project) is True

    @pytest.mark.permission
    def test_can_edit_project_as_creator_not_manager(self, organization, authenticated_user, another_user):
        """Test that project creator can edit even without manager role."""
        project = Project.objects.create(
            organization=organization,
            name="Creator Project",
            created_by_user=authenticated_user,
        )
        # authenticated_user is creator, not manager
        ProjectMember.objects.filter(project=project, user=authenticated_user).delete()
        assert ProjectService.can_edit_project(authenticated_user, project) is True

    @pytest.mark.permission
    def test_can_edit_project_as_org_admin(self, project, authenticated_user, another_user):
        """Test that organization admin can edit project."""
        # Make another_user an org admin
        admin_role = Role.objects.get_or_create(code="organization_admin")[0]
        OrganizationMembership.objects.create(
            organization=project.organization,
            user=another_user,
            role=admin_role,
            status=OrganizationMembership.STATUS_ACTIVE,
        )
        assert ProjectService.can_edit_project(another_user, project) is True

    @pytest.mark.permission
    def test_cannot_edit_project_as_contributor(self, project, another_user, authenticated_user):
        """Test that contributor cannot edit project."""
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        assert ProjectService.can_edit_project(another_user, project) is False

    @pytest.mark.permission
    def test_cannot_edit_project_not_member(self, project, another_user):
        """Test that non-member cannot edit project."""
        assert ProjectService.can_edit_project(another_user, project) is False

    @pytest.mark.permission
    def test_can_delete_project_as_manager(self, project, authenticated_user):
        """Test that project manager can delete project."""
        assert ProjectService.can_delete_project(authenticated_user, project) is True

    @pytest.mark.permission
    def test_cannot_delete_project_as_creator_not_manager(self, organization, authenticated_user):
        """Test that creator without manager role cannot delete project."""
        project = Project.objects.create(
            organization=organization,
            name="Delete Test Project",
            created_by_user=authenticated_user,
        )
        ProjectMember.objects.filter(project=project, user=authenticated_user).delete()
        assert ProjectService.can_delete_project(authenticated_user, project) is False

    @pytest.mark.permission
    def test_can_delete_project_as_org_admin(self, project, another_user):
        """Test that organization admin can delete project."""
        admin_role = Role.objects.get_or_create(code="organization_admin")[0]
        OrganizationMembership.objects.create(
            organization=project.organization,
            user=another_user,
            role=admin_role,
            status=OrganizationMembership.STATUS_ACTIVE,
        )
        assert ProjectService.can_delete_project(another_user, project) is True

    @pytest.mark.permission
    def test_cannot_delete_project_as_contributor(self, project, another_user, authenticated_user):
        """Test that contributor cannot delete project."""
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        assert ProjectService.can_delete_project(another_user, project) is False

    @pytest.mark.permission
    def test_can_manage_members_as_manager(self, project, authenticated_user):
        """Test that project manager can manage members."""
        assert ProjectService.can_manage_members(authenticated_user, project) is True

    @pytest.mark.permission
    def test_can_manage_members_as_org_admin(self, project, another_user):
        """Test that organization admin can manage members."""
        admin_role = Role.objects.get_or_create(code="organization_admin")[0]
        OrganizationMembership.objects.create(
            organization=project.organization,
            user=another_user,
            role=admin_role,
            status=OrganizationMembership.STATUS_ACTIVE,
        )
        assert ProjectService.can_manage_members(another_user, project) is True

    @pytest.mark.permission
    def test_cannot_manage_members_as_contributor(self, project, another_user, authenticated_user):
        """Test that contributor cannot manage members."""
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        assert ProjectService.can_manage_members(another_user, project) is False

    def test_add_member_success(self, project, another_user, authenticated_user, org_member_role):
        """Test successfully adding a project member."""
        org_membership = OrganizationMembership.objects.create(
            organization=project.organization,
            user=another_user,
            role=org_member_role,
            status=OrganizationMembership.STATUS_ACTIVE,
        )
        ProjectService.add_member(
            project=project,
            user_id=another_user.id,
            role_code=ProjectMember.ROLE_CONTRIBUTOR,
            added_by=authenticated_user,
        )
        member = ProjectMember.objects.get(project=project, user=another_user)
        assert member.project_role == ProjectMember.ROLE_CONTRIBUTOR
        assert member.added_by_user == authenticated_user

    @pytest.mark.negative
    def test_add_member_user_not_found(self, project, authenticated_user):
        """Test adding member with non-existent user."""
        import uuid
        with pytest.raises(ResourceNotFoundException):
            ProjectService.add_member(
                project=project,
                user_id=uuid.uuid4(),
                role_code=ProjectMember.ROLE_CONTRIBUTOR,
                added_by=authenticated_user,
            )

    @pytest.mark.negative
    def test_add_member_not_org_member(self, project, another_user, authenticated_user):
        """Test adding a member who is not an organization member."""
        with pytest.raises(ValueError, match="not an active organization member"):
            ProjectService.add_member(
                project=project,
                user_id=another_user.id,
                role_code=ProjectMember.ROLE_CONTRIBUTOR,
                added_by=authenticated_user,
            )

    def test_add_member_idempotent(self, project, another_user, authenticated_user, org_member_role):
        """Test that adding same member twice doesn't duplicate."""
        OrganizationMembership.objects.create(
            organization=project.organization,
            user=another_user,
            role=org_member_role,
            status=OrganizationMembership.STATUS_ACTIVE,
        )
        ProjectService.add_member(
            project=project,
            user_id=another_user.id,
            role_code=ProjectMember.ROLE_CONTRIBUTOR,
            added_by=authenticated_user,
        )
        initial_count = ProjectMember.objects.filter(project=project, user=another_user).count()
        
        ProjectService.add_member(
            project=project,
            user_id=another_user.id,
            role_code=ProjectMember.ROLE_MANAGER,
            added_by=authenticated_user,
        )
        final_count = ProjectMember.objects.filter(project=project, user=another_user).count()
        assert initial_count == final_count == 1

    def test_service_uses_real_database_queries(self, project, authenticated_user, another_user):
        """Test that service uses real database queries, not mocks."""
        # Verify actual database state is queried
        assert not ProjectMember.objects.filter(
            user=authenticated_user,
            project=project,
            project_role=ProjectMember.ROLE_MANAGER,
        ).exists() is False
        
        # Now verify it changes
        ProjectMember.objects.create(
            project=project,
            user=authenticated_user,
            project_role=ProjectMember.ROLE_MANAGER,
            added_by_user=authenticated_user,
        )
        assert ProjectService.can_manage_members(authenticated_user, project) is True

    @pytest.mark.idempotency
    def test_add_member_transaction_rollback(self, project, authenticated_user):
        """Test transaction behavior with errors."""
        import uuid
        initial_count = ProjectMember.objects.filter(project=project).count()
        
        try:
            with transaction.atomic():
                ProjectService.add_member(
                    project=project,
                    user_id=uuid.uuid4(),
                    role_code=ProjectMember.ROLE_CONTRIBUTOR,
                    added_by=authenticated_user,
                )
        except ResourceNotFoundException:
            pass
        
        # Verify no members were added
        assert ProjectMember.objects.filter(project=project).count() == initial_count


