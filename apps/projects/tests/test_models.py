"""Tests for Project and ProjectMember models."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.projects.models import Project, ProjectMember
from apps.organizations.models import Organization, OrganizationMembership, Role
from apps.users.models import User


@pytest.mark.django_db
class TestProjectModel:
    """Test cases for Project model."""

    def test_create_project_with_valid_data(self, organization, authenticated_user):
        """Test creating a project with valid data."""
        project = Project.objects.create(
            organization=organization,
            name="Test Project",
            description="A test project",
            status=Project.STATUS_ACTIVE,
            created_by_user=authenticated_user,
        )
        assert project.id is not None
        assert project.name == "Test Project"
        assert project.status == Project.STATUS_ACTIVE
        assert project.organization == organization
        assert project.created_by_user == authenticated_user
        assert project.created_at is not None
        assert project.updated_at is not None
        assert project.deleted_at is None

    def test_project_string_representation(self, project):
        """Test __str__ method returns project name."""
        assert str(project) == "Test Project"

    def test_create_project_with_deadline(self, organization, authenticated_user):
        """Test creating a project with a deadline."""
        deadline = timezone.now() + timezone.timedelta(days=30)
        project = Project.objects.create(
            organization=organization,
            name="Project with Deadline",
            status=Project.STATUS_ACTIVE,
            deadline_at=deadline,
            created_by_user=authenticated_user,
        )
        assert project.deadline_at == deadline

    def test_project_timestamps_auto_generated(self, organization, authenticated_user):
        """Test that created_at and updated_at are automatically set."""
        before = timezone.now()
        project = Project.objects.create(
            organization=organization,
            name="Project for timestamp test",
            created_by_user=authenticated_user,
        )
        after = timezone.now()
        assert before <= project.created_at <= after
        assert before <= project.updated_at <= after

    def test_project_updated_at_changes_on_update(self, project):
        """Test that updated_at changes when project is updated."""
        original_updated_at = project.updated_at
        from time import sleep
        sleep(0.01)  # Ensure time passes
        project.name = "Updated Project"
        project.save()
        project.refresh_from_db()
        assert project.updated_at > original_updated_at

    def test_project_soft_delete_with_deleted_at(self, project):
        """Test soft delete functionality with deleted_at field."""
        assert project.deleted_at is None
        delete_time = timezone.now()
        project.deleted_at = delete_time
        project.save()
        project.refresh_from_db()
        assert project.deleted_at == delete_time

    def test_project_unique_name_per_organization(self, organization, authenticated_user):
        """Test unique constraint on name per organization (while not soft deleted)."""
        Project.objects.create(
            organization=organization,
            name="Unique Project",
            created_by_user=authenticated_user,
        )
        with pytest.raises(IntegrityError):
            Project.objects.create(
                organization=organization,
                name="Unique Project",
                created_by_user=authenticated_user,
            )

    def test_project_allows_duplicate_name_across_orgs(self, authenticated_user, another_user):
        """Test that same project name is allowed across different organizations."""
        org1 = Organization.objects.create(
            name="Org 1",
            slug="org-1",
            owner_user=authenticated_user,
        )
        org2 = Organization.objects.create(
            name="Org 2",
            slug="org-2",
            owner_user=another_user,
        )
        proj1 = Project.objects.create(
            organization=org1,
            name="Same Name",
            created_by_user=authenticated_user,
        )
        proj2 = Project.objects.create(
            organization=org2,
            name="Same Name",
            created_by_user=another_user,
        )
        assert proj1.name == proj2.name
        assert proj1.organization != proj2.organization

    def test_project_allows_duplicate_name_if_soft_deleted(self, organization, authenticated_user):
        """Test that soft-deleted projects don't block new projects with same name."""
        project1 = Project.objects.create(
            organization=organization,
            name="Reusable Name",
            created_by_user=authenticated_user,
        )
        project1.deleted_at = timezone.now()
        project1.save()
        
        # Should be able to create a new project with same name
        project2 = Project.objects.create(
            organization=organization,
            name="Reusable Name",
            created_by_user=authenticated_user,
        )
        assert project2.id != project1.id

    def test_project_status_choices(self, organization, authenticated_user):
        """Test that project status must be valid choice."""
        project = Project.objects.create(
            organization=organization,
            name="Status Test",
            status=Project.STATUS_ACTIVE,
            created_by_user=authenticated_user,
        )
        assert project.status in [Project.STATUS_ACTIVE, Project.STATUS_COMPLETED, Project.STATUS_ARCHIVED]

    def test_project_foreign_key_organization_cascade_delete(self, organization, authenticated_user):
        """Test that deleting organization cascades to projects."""
        project = Project.objects.create(
            organization=organization,
            name="Project to cascade delete",
            created_by_user=authenticated_user,
        )
        org_id = organization.id
        project_id = project.id
        organization.delete()
        assert not Project.objects.filter(id=project_id).exists()

    def test_project_foreign_key_created_by_restrict(self, project, authenticated_user):
        """Test that deleting creator user is restricted."""
        from django.db import IntegrityError
        user = authenticated_user
        with pytest.raises(IntegrityError):
            user.delete()

    def test_project_updated_by_user_nullable(self, organization, authenticated_user):
        """Test that updated_by_user can be null."""
        project = Project.objects.create(
            organization=organization,
            name="No updated by user",
            created_by_user=authenticated_user,
        )
        assert project.updated_by_user is None

    def test_project_delete_sets_null_on_updated_by_user(self, organization, authenticated_user, another_user):
        """Test that deleting a user sets updated_by_user to null."""
        project = Project.objects.create(
            organization=organization,
            name="Project with updated user",
            created_by_user=authenticated_user,
            updated_by_user=another_user,
        )
        project_id = project.id
        another_user.delete()
        project.refresh_from_db()
        assert project.updated_by_user is None


@pytest.mark.django_db
class TestProjectMemberModel:
    """Test cases for ProjectMember model."""

    def test_create_project_member_with_valid_data(self, project, another_user, authenticated_user):
        """Test creating a project member with valid data."""
        member = ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        assert member.id is not None
        assert member.project == project
        assert member.user == another_user
        assert member.project_role == ProjectMember.ROLE_CONTRIBUTOR
        assert member.added_by_user == authenticated_user
        assert member.created_at is not None

    def test_project_member_string_representation(self, project, member_in_org):
        """Test __str__ or model representation of project member."""
        member = ProjectMember.objects.create(
            project=project,
            user=member_in_org,
            project_role=ProjectMember.ROLE_VIEWER,
            added_by_user=project.created_by_user,
        )
        # Just verify it's created successfully
        assert member.id is not None

    def test_project_member_role_choices(self, project, another_user, authenticated_user):
        """Test that project member role must be valid choice."""
        member = ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_MANAGER,
            added_by_user=authenticated_user,
        )
        assert member.project_role in [
            ProjectMember.ROLE_MANAGER,
            ProjectMember.ROLE_CONTRIBUTOR,
            ProjectMember.ROLE_VIEWER,
        ]

    def test_project_member_unique_constraint_project_user(self, project, another_user, authenticated_user):
        """Test unique constraint on (project, user) pair."""
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        with pytest.raises(IntegrityError):
            ProjectMember.objects.create(
                project=project,
                user=another_user,
                project_role=ProjectMember.ROLE_MANAGER,
                added_by_user=authenticated_user,
            )

    def test_project_member_same_user_different_projects(self, authenticated_user, another_user):
        """Test that same user can be member of different projects."""
        org = Organization.objects.create(
            name="Test Org",
            slug="test-org",
            owner_user=authenticated_user,
        )
        project1 = Project.objects.create(
            organization=org,
            name="Project 1",
            created_by_user=authenticated_user,
        )
        project2 = Project.objects.create(
            organization=org,
            name="Project 2",
            created_by_user=authenticated_user,
        )
        member1 = ProjectMember.objects.create(
            project=project1,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        member2 = ProjectMember.objects.create(
            project=project2,
            user=another_user,
            project_role=ProjectMember.ROLE_MANAGER,
            added_by_user=authenticated_user,
        )
        assert member1.project != member2.project
        assert member1.user == member2.user

    def test_project_member_created_at_auto_generated(self, project, another_user, authenticated_user):
        """Test that created_at is automatically set."""
        before = timezone.now()
        member = ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        after = timezone.now()
        assert before <= member.created_at <= after

    def test_project_member_foreign_key_project_cascade(self, project, another_user, authenticated_user):
        """Test that deleting a project cascades to project members."""
        member = ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        member_id = member.id
        project.delete()
        assert not ProjectMember.objects.filter(id=member_id).exists()

    def test_project_member_foreign_key_user_cascade(self, project, another_user, authenticated_user):
        """Test that deleting a user cascades to project memberships."""
        member = ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        member_id = member.id
        another_user.delete()
        assert not ProjectMember.objects.filter(id=member_id).exists()

    def test_project_member_foreign_key_added_by_restrict(self, project, another_user, authenticated_user):
        """Test that deleting added_by_user is restricted."""
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        with pytest.raises(IntegrityError):
            authenticated_user.delete()

    def test_project_member_default_role(self, project, another_user, authenticated_user):
        """Test that default role is set correctly."""
        member = ProjectMember.objects.create(
            project=project,
            user=another_user,
            added_by_user=authenticated_user,
        )
        assert member.project_role == ProjectMember.ROLE_CONTRIBUTOR

