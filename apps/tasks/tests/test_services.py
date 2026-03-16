"""Tests for Task service business logic."""

import pytest
from django.db import transaction

from apps.tasks.models import Task
from apps.tasks.services import TaskService
from apps.projects.models import ProjectMember, Project
from apps.core.exceptions import ResourceNotFoundException
from apps.organizations.models import Organization


@pytest.mark.django_db
class TestTaskService:
    """Test cases for TaskService methods."""

    @pytest.mark.permission
    def test_can_update_task_as_manager(self, task, authenticated_user):
        """Test that project manager can update task."""
        assert ProjectMember.objects.filter(
            user=authenticated_user,
            project=task.project,
            project_role=ProjectMember.ROLE_MANAGER,
        ).exists()
        assert TaskService.can_update_task(authenticated_user, task) is True

    @pytest.mark.permission
    def test_can_update_task_as_creator(self, project, authenticated_user, another_user):
        """Test that task creator can update task."""
        task = Task.objects.create(
            project=project,
            title="Creator Task",
            created_by_user=authenticated_user,
        )
        # Remove as manager
        ProjectMember.objects.filter(
            user=authenticated_user,
            project=project,
            project_role=ProjectMember.ROLE_MANAGER,
        ).update(project_role=ProjectMember.ROLE_CONTRIBUTOR)
        
        assert TaskService.can_update_task(authenticated_user, task) is True

    @pytest.mark.permission
    def test_can_update_task_as_assignee(self, project, authenticated_user, another_user):
        """Test that task assignee can update task."""
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        task = Task.objects.create(
            project=project,
            title="Assigned Task",
            assignee_user=another_user,
            created_by_user=authenticated_user,
        )
        assert TaskService.can_update_task(another_user, task) is True

    @pytest.mark.permission
    def test_cannot_update_task_not_creator_or_assignee(self, project, authenticated_user, another_user):
        """Test that non-creator/assignee cannot update without manager role."""
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        task = Task.objects.create(
            project=project,
            title="Other Task",
            created_by_user=authenticated_user,
        )
        assert TaskService.can_update_task(another_user, task) is False

    @pytest.mark.permission
    def test_can_delete_task_as_manager(self, task, authenticated_user):
        """Test that project manager can delete task."""
        assert TaskService.can_delete_task(authenticated_user, task) is True

    @pytest.mark.permission
    def test_can_delete_task_as_creator(self, project, authenticated_user):
        """Test that task creator can delete task."""
        task = Task.objects.create(
            project=project,
            title="Creator Delete",
            created_by_user=authenticated_user,
        )
        ProjectMember.objects.filter(
            user=authenticated_user,
            project=project,
            project_role=ProjectMember.ROLE_MANAGER,
        ).update(project_role=ProjectMember.ROLE_CONTRIBUTOR)
        
        assert TaskService.can_delete_task(authenticated_user, task) is True

    @pytest.mark.permission
    def test_cannot_delete_task_as_contributor_non_creator(self, project, authenticated_user, another_user):
        """Test that contributor cannot delete task they didn't create."""
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        task = Task.objects.create(
            project=project,
            title="Other's Task",
            created_by_user=authenticated_user,
        )
        assert TaskService.can_delete_task(another_user, task) is False

    def test_validate_task_creation_success(self, organization, project, authenticated_user, another_user):
        """Test successful task creation validation."""
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        validated_data = {
            "project_id": project.id,
            "assignee_user_id": another_user.id,
            "title": "New Task",
        }
        # Should not raise
        TaskService.validate_task_creation(organization.id, validated_data, authenticated_user)

    @pytest.mark.negative
    def test_validate_task_creation_project_not_found(self, organization, authenticated_user):
        """Test validation fails if project doesn't exist."""
        import uuid
        validated_data = {
            "project_id": uuid.uuid4(),
            "title": "Missing Project",
        }
        with pytest.raises(ResourceNotFoundException):
            TaskService.validate_task_creation(organization.id, validated_data, authenticated_user)

    @pytest.mark.negative
    def test_validate_task_creation_project_wrong_org(self, organization, another_user, authenticated_user):
        """Test validation fails if project in different org."""
        other_org = Organization.objects.create(
            name="Other Org",
            slug="other-org",
            owner_user=another_user,
        )
        project = Project.objects.create(
            organization=other_org,
            name="Other Project",
            created_by_user=another_user,
        )
        validated_data = {
            "project_id": project.id,
            "title": "Wrong Org",
        }
        with pytest.raises(ResourceNotFoundException):
            TaskService.validate_task_creation(organization.id, validated_data, authenticated_user)

    @pytest.mark.negative
    def test_validate_task_creation_assignee_not_member(self, organization, project, authenticated_user, another_user):
        """Test validation fails if assignee is not project member."""
        validated_data = {
            "project_id": project.id,
            "assignee_user_id": another_user.id,
            "title": "Wrong Assignee",
        }
        with pytest.raises(ValueError, match="not a project member"):
            TaskService.validate_task_creation(organization.id, validated_data, authenticated_user)

    def test_validate_task_creation_no_assignee(self, organization, project, authenticated_user):
        """Test that assignee is optional."""
        validated_data = {
            "project_id": project.id,
            "title": "No Assignee",
        }
        # Should not raise
        TaskService.validate_task_creation(organization.id, validated_data, authenticated_user)

    def test_service_uses_real_database_queries(self, task, authenticated_user, another_user):
        """Test that service uses real database queries."""
        # Verify initial state
        assert not ProjectMember.objects.filter(
            user=authenticated_user,
            project=task.project,
            project_role=ProjectMember.ROLE_VIEWER,
        ).exists()
        
        # Update database
        ProjectMember.objects.filter(
            user=authenticated_user,
            project=task.project,
        ).update(project_role=ProjectMember.ROLE_VIEWER)
        
        # Verify service sees updated state
        assert TaskService.can_update_task(authenticated_user, task) is False

    @pytest.mark.idempotency
    def test_task_creation_validation_transaction_rollback(self, organization, authenticated_user):
        """Test transaction behavior on validation errors."""
        import uuid
        initial_count = Task.objects.count()
        
        try:
            with transaction.atomic():
                TaskService.validate_task_creation(
                    organization.id,
                    {"project_id": uuid.uuid4(), "title": "Bad"},
                    authenticated_user,
                )
        except ResourceNotFoundException:
            pass
        
        # Verify no tasks were created
        assert Task.objects.count() == initial_count


