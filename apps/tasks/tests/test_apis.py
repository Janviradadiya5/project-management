"""Tests for Task REST API endpoints."""

import pytest
from rest_framework import status
from django.utils import timezone

from apps.tasks.models import Task
from apps.projects.models import Project, ProjectMember


@pytest.mark.django_db
class TestTaskListApi:
    """Test cases for Task list endpoint."""

    @pytest.mark.auth
    def test_list_tasks_authentication_required(self, api_client, organization):
        """Test that authentication is required."""
        response = api_client.get(
            "/api/v1/tasks/",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_tasks_success(self, authenticated_client, project, authenticated_user):
        """Test successfully listing tasks."""
        Task.objects.create(
            project=project,
            title="Task 1",
            created_by_user=authenticated_user,
        )
        Task.objects.create(
            project=project,
            title="Task 2",
            created_by_user=authenticated_user,
        )
        
        response = authenticated_client.get(
            "/api/v1/tasks/",
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_list_tasks_pagination(self, authenticated_client, project, authenticated_user):
        """Test task list pagination."""
        for i in range(15):
            Task.objects.create(
                project=project,
                title=f"Task {i}",
                created_by_user=authenticated_user,
            )
        
        response = authenticated_client.get(
            "/api/v1/tasks/?page=1",
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert "next" in response.data

    def test_list_tasks_filter_by_status(self, authenticated_client, project, authenticated_user):
        """Test filtering tasks by status."""
        Task.objects.create(
            project=project,
            title="Todo Task",
            status=Task.STATUS_TODO,
            created_by_user=authenticated_user,
        )
        Task.objects.create(
            project=project,
            title="Done Task",
            status=Task.STATUS_DONE,
            completed_at=timezone.now(),
            created_by_user=authenticated_user,
        )
        
        response = authenticated_client.get(
            f"/api/v1/tasks/?status={Task.STATUS_TODO}",
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["status"] == Task.STATUS_TODO

    def test_list_tasks_filter_by_priority(self, authenticated_client, project, authenticated_user):
        """Test filtering tasks by priority."""
        Task.objects.create(
            project=project,
            title="High Priority",
            priority=Task.PRIORITY_HIGH,
            created_by_user=authenticated_user,
        )
        Task.objects.create(
            project=project,
            title="Low Priority",
            priority=Task.PRIORITY_LOW,
            created_by_user=authenticated_user,
        )
        
        response = authenticated_client.get(
            f"/api/v1/tasks/?priority={Task.PRIORITY_HIGH}",
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_tasks_search_by_title(self, authenticated_client, project, authenticated_user):
        """Test searching tasks by title."""
        Task.objects.create(
            project=project,
            title="API Documentation",
            created_by_user=authenticated_user,
        )
        Task.objects.create(
            project=project,
            title="Database Schema",
            created_by_user=authenticated_user,
        )
        
        response = authenticated_client.get(
            "/api/v1/tasks/?search=API",
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1


@pytest.mark.django_db
class TestTaskCreateApi:
    """Test cases for Task creation endpoint."""

    def test_create_task_success(self, authenticated_client, project):
        """Test successfully creating a task."""
        response = authenticated_client.post(
            "/api/v1/tasks/",
            {
                "project_id": str(project.id),
                "title": "New Task",
                "description": "A new task",
                "priority": "medium",
                "status": "todo",
            },
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["title"] == "New Task"
        assert response.data["success"] is True

    @pytest.mark.negative
    def test_create_task_title_required(self, authenticated_client, project):
        """Test that title is required."""
        response = authenticated_client.post(
            "/api/v1/tasks/",
            {
                "project_id": str(project.id),
            },
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.negative
    def test_create_task_title_too_short(self, authenticated_client, project):
        """Test that title must be at least 2 characters."""
        response = authenticated_client.post(
            "/api/v1/tasks/",
            {
                "project_id": str(project.id),
                "title": "A",
            },
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.negative
    def test_create_task_invalid_priority(self, authenticated_client, project):
        """Test that invalid priority is rejected."""
        response = authenticated_client.post(
            "/api/v1/tasks/",
            {
                "project_id": str(project.id),
                "title": "Bad Priority",
                "priority": "urgent",
            },
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.negative
    def test_create_task_invalid_status(self, authenticated_client, project):
        """Test that invalid status is rejected."""
        response = authenticated_client.post(
            "/api/v1/tasks/",
            {
                "project_id": str(project.id),
                "title": "Bad Status",
                "status": "invalid",
            },
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.negative
    def test_create_task_assignee_not_member(self, authenticated_client, project, another_user):
        """Test that assigning non-member fails."""
        response = authenticated_client.post(
            "/api/v1/tasks/",
            {
                "project_id": str(project.id),
                "title": "Bad Assignee",
                "assignee_user_id": str(another_user.id),
            },
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
            format="json",
        )
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT]

    def test_create_task_with_assignee(self, authenticated_client, project, authenticated_user, another_user):
        """Test creating task with valid assignee."""
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        
        response = authenticated_client.post(
            "/api/v1/tasks/",
            {
                "project_id": str(project.id),
                "title": "Assigned Task",
                "assignee_user_id": str(another_user.id),
            },
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_task_sets_created_by_user(self, authenticated_client, project, authenticated_user):
        """Test that created_by_user is set to current user."""
        response = authenticated_client.post(
            "/api/v1/tasks/",
            {
                "project_id": str(project.id),
                "title": "Creator Test",
            },
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        task = Task.objects.get(id=response.data["data"]["id"])
        assert task.created_by_user == authenticated_user


@pytest.mark.django_db
class TestTaskDetailApi:
    """Test cases for Task detail endpoint."""

    def test_get_task_detail_success(self, authenticated_client, task):
        """Test successfully retrieving task details."""
        response = authenticated_client.get(
            f"/api/v1/tasks/{task.id}/",
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == task.title

    @pytest.mark.negative
    def test_get_task_not_found(self, authenticated_client, organization):
        """Test getting non-existent task returns 404."""
        import uuid
        response = authenticated_client.get(
            f"/api/v1/tasks/{uuid.uuid4()}/",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_task_success(self, authenticated_client, task):
        """Test successfully updating a task."""
        response = authenticated_client.patch(
            f"/api/v1/tasks/{task.id}/",
            {
                "title": "Updated Task",
                "status": "in_progress",
            },
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.title == "Updated Task"
        assert task.status == Task.STATUS_IN_PROGRESS

    @pytest.mark.permission
    def test_update_task_permission_denied(self, authenticated_user, another_user):
        """Test that unauthorized user cannot update task."""
        from apps.organizations.models import Organization
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        org = Organization.objects.create(
            name="Test Org",
            slug="test-org",
            owner_user=authenticated_user,
        )
        project = Project.objects.create(
            organization=org,
            name="Test Project",
            created_by_user=authenticated_user,
        )
        task = Task.objects.create(
            project=project,
            title="Restricted Task",
            created_by_user=authenticated_user,
        )
        
        # Add another_user as viewer (no update permissions)
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_VIEWER,
            added_by_user=authenticated_user,
        )
        
        client = APIClient()
        refresh = RefreshToken.for_user(another_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        response = client.patch(
            f"/api/v1/tasks/{task.id}/",
            {
                "title": "Hacked",
            },
            HTTP_X_ORGANIZATION_ID=str(org.id),
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_task_success(self, authenticated_client, task):
        """Test successfully deleting a task."""
        task_id = task.id
        response = authenticated_client.delete(
            f"/api/v1/tasks/{task_id}/",
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]
        assert not Task.objects.filter(id=task_id).exists()

    @pytest.mark.permission
    def test_delete_task_permission_denied(self, authenticated_user, another_user):
        """Test that contributor cannot delete others' tasks."""
        from apps.organizations.models import Organization
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        org = Organization.objects.create(
            name="Test Org",
            slug="test-org",
            owner_user=authenticated_user,
        )
        project = Project.objects.create(
            organization=org,
            name="Test Project",
            created_by_user=authenticated_user,
        )
        task = Task.objects.create(
            project=project,
            title="Delete Test",
            created_by_user=authenticated_user,
        )
        
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        
        client = APIClient()
        refresh = RefreshToken.for_user(another_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        response = client.delete(
            f"/api/v1/tasks/{task.id}/",
            HTTP_X_ORGANIZATION_ID=str(org.id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.auth
    def test_task_detail_requires_authentication(self, api_client, task):
        """Test that authentication is required."""
        response = api_client.get(
            f"/api/v1/tasks/{task.id}/",
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


