"""Tests for Project REST API endpoints."""

import pytest
from rest_framework import status
from django.utils import timezone

from apps.projects.models import Project, ProjectMember
from apps.organizations.models import OrganizationMembership, Role


@pytest.mark.django_db
class TestProjectListApi:
    """Test cases for Project list endpoint."""

    @pytest.mark.auth
    def test_list_projects_authentication_required(self, api_client, organization):
        """Test that authentication is required for list projects."""
        response = api_client.get(
            "/api/v1/projects/",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_projects_success(self, authenticated_client, organization, authenticated_user):
        """Test successfully listing projects."""
        Project.objects.create(
            organization=organization,
            name="Project 1",
            created_by_user=authenticated_user,
        )
        Project.objects.create(
            organization=organization,
            name="Project 2",
            created_by_user=authenticated_user,
        )
        
        response = authenticated_client.get(
            "/api/v1/projects/",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_list_projects_pagination(self, authenticated_client, organization, authenticated_user):
        """Test project list pagination."""
        for i in range(15):
            Project.objects.create(
                organization=organization,
                name=f"Project {i}",
                created_by_user=authenticated_user,
            )
        
        response = authenticated_client.get(
            "/api/v1/projects/?page=1",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert "next" in response.data
        assert response.data["count"] == 15

    def test_list_projects_filter_by_status(self, authenticated_client, organization, authenticated_user):
        """Test filtering projects by status."""
        Project.objects.create(
            organization=organization,
            name="Active Project",
            status=Project.STATUS_ACTIVE,
            created_by_user=authenticated_user,
        )
        Project.objects.create(
            organization=organization,
            name="Archived Project",
            status=Project.STATUS_ARCHIVED,
            created_by_user=authenticated_user,
        )
        
        response = authenticated_client.get(
            f"/api/v1/projects/?status={Project.STATUS_ACTIVE}",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["status"] == Project.STATUS_ACTIVE

    def test_list_projects_search_by_name(self, authenticated_client, organization, authenticated_user):
        """Test searching projects by name."""
        Project.objects.create(
            organization=organization,
            name="Python Backend",
            created_by_user=authenticated_user,
        )
        Project.objects.create(
            organization=organization,
            name="React Frontend",
            created_by_user=authenticated_user,
        )
        
        response = authenticated_client.get(
            "/api/v1/projects/?search=Python",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_projects_ordering(self, authenticated_client, organization, authenticated_user):
        """Test ordering projects."""
        Project.objects.create(
            organization=organization,
            name="First Project",
            created_by_user=authenticated_user,
        )
        Project.objects.create(
            organization=organization,
            name="Second Project",
            created_by_user=authenticated_user,
        )
        
        response = authenticated_client.get(
            "/api/v1/projects/?ordering=-created_at",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["name"] == "Second Project"

    @pytest.mark.permission
    def test_list_projects_organization_isolation(self, authenticated_client, authenticated_user, another_user):
        """Test that users only see projects from their organization."""
        from apps.organizations.models import Organization
        
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
        
        Project.objects.create(
            organization=org1,
            name="Org 1 Project",
            created_by_user=authenticated_user,
        )
        Project.objects.create(
            organization=org2,
            name="Org 2 Project",
            created_by_user=another_user,
        )
        
        response = authenticated_client.get(
            "/api/v1/projects/",
            HTTP_X_ORGANIZATION_ID=str(org1.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Org 1 Project"


@pytest.mark.django_db
class TestProjectCreateApi:
    """Test cases for Project creation endpoint."""

    def test_create_project_success(self, authenticated_client, organization):
        """Test successfully creating a project."""
        response = authenticated_client.post(
            "/api/v1/projects/",
            {
                "name": "New Project",
                "description": "A new project",
                "status": "active",
            },
            HTTP_X_ORGANIZATION_ID=str(organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["name"] == "New Project"
        assert response.data["success"] is True

    @pytest.mark.negative
    def test_create_project_validation_error_empty_name(self, authenticated_client, organization):
        """Test that empty name is rejected."""
        response = authenticated_client.post(
            "/api/v1/projects/",
            {
                "name": "",
            },
            HTTP_X_ORGANIZATION_ID=str(organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.negative
    def test_create_project_validation_error_name_too_short(self, authenticated_client, organization):
        """Test that name with less than 2 chars is rejected."""
        response = authenticated_client.post(
            "/api/v1/projects/",
            {
                "name": "A",
            },
            HTTP_X_ORGANIZATION_ID=str(organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.negative
    def test_create_project_validation_error_name_too_long(self, authenticated_client, organization):
        """Test that name exceeding 200 chars is rejected."""
        response = authenticated_client.post(
            "/api/v1/projects/",
            {
                "name": "A" * 201,
            },
            HTTP_X_ORGANIZATION_ID=str(organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.negative
    def test_create_project_validation_error_invalid_status(self, authenticated_client, organization):
        """Test that invalid status is rejected."""
        response = authenticated_client.post(
            "/api/v1/projects/",
            {
                "name": "Project",
                "status": "invalid",
            },
            HTTP_X_ORGANIZATION_ID=str(organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.negative
    def test_create_project_validation_error_xss_in_name(self, authenticated_client, organization):
        """Test that XSS attempts in name are rejected."""
        response = authenticated_client.post(
            "/api/v1/projects/",
            {
                "name": "<script>alert('xss')</script>",
            },
            HTTP_X_ORGANIZATION_ID=str(organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_project_with_deadline(self, authenticated_client, organization):
        """Test creating project with deadline."""
        deadline = timezone.now() + timezone.timedelta(days=30)
        response = authenticated_client.post(
            "/api/v1/projects/",
            {
                "name": "Project with Deadline",
                "deadline_at": deadline.isoformat(),
            },
            HTTP_X_ORGANIZATION_ID=str(organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.negative
    def test_create_project_deadline_in_past(self, authenticated_client, organization):
        """Test that deadline in the past is rejected."""
        past = timezone.now() - timezone.timedelta(days=1)
        response = authenticated_client.post(
            "/api/v1/projects/",
            {
                "name": "Past Deadline",
                "deadline_at": past.isoformat(),
            },
            HTTP_X_ORGANIZATION_ID=str(organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_project_sets_created_by_user(self, authenticated_client, organization, authenticated_user):
        """Test that created_by_user is set to current user."""
        response = authenticated_client.post(
            "/api/v1/projects/",
            {
                "name": "User Project",
            },
            HTTP_X_ORGANIZATION_ID=str(organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        project = Project.objects.get(id=response.data["data"]["id"])
        assert project.created_by_user == authenticated_user

    def test_create_project_response_envelope(self, authenticated_client, organization):
        """Test response envelope structure."""
        response = authenticated_client.post(
            "/api/v1/projects/",
            {
                "name": "Envelope Test",
            },
            HTTP_X_ORGANIZATION_ID=str(organization.id),
            format="json",
        )
        assert "success" in response.data
        assert "message" in response.data
        assert "data" in response.data
        assert response.data["success"] is True


@pytest.mark.django_db
class TestProjectDetailApi:
    """Test cases for Project detail endpoint."""

    def test_get_project_detail_success(self, authenticated_client, project):
        """Test successfully retrieving project details."""
        response = authenticated_client.get(
            f"/api/v1/projects/{project.id}/",
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == project.name

    @pytest.mark.negative
    def test_get_project_detail_not_found(self, authenticated_client, organization):
        """Test getting non-existent project returns 404."""
        import uuid
        response = authenticated_client.get(
            f"/api/v1/projects/{uuid.uuid4()}/",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_project_success(self, authenticated_client, project, authenticated_user):
        """Test successfully updating a project."""
        response = authenticated_client.patch(
            f"/api/v1/projects/{project.id}/",
            {
                "name": "Updated Project",
                "status": "archived",
            },
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["name"] == "Updated Project"
        project.refresh_from_db()
        assert project.name == "Updated Project"

    @pytest.mark.permission
    def test_update_project_permission_denied(self, authenticated_client, authenticated_user, another_user):
        """Test that non-manager cannot update project."""
        org = authenticated_user.organizations.first()
        from apps.organizations.models import Organization
        org = Organization.objects.create(
            name="Org",
            slug="org",
            owner_user=authenticated_user,
        )
        project = Project.objects.create(
            organization=org,
            name="Test",
            created_by_user=authenticated_user,
        )
        
        # Remove authenticated_user from project members
        ProjectMember.objects.filter(project=project).delete()
        
        # Add another_user as contributor
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        
        # Try to update with another_user
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        client = APIClient()
        refresh = RefreshToken.for_user(another_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        response = client.patch(
            f"/api/v1/projects/{project.id}/",
            {
                "name": "Hacked",
            },
            HTTP_X_ORGANIZATION_ID=str(org.id),
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_project_success(self, authenticated_client, project):
        """Test successfully deleting a project."""
        project_id = project.id
        response = authenticated_client.delete(
            f"/api/v1/projects/{project_id}/",
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
        )
        assert response.status_code == status.HTTP_200_OK or response.status_code == status.HTTP_204_NO_CONTENT
        assert not Project.objects.filter(id=project_id).exists()

    @pytest.mark.permission
    def test_delete_project_permission_denied(self, authenticated_client, authenticated_user, another_user):
        """Test that contributor cannot delete project."""
        from apps.organizations.models import Organization
        org = Organization.objects.create(
            name="Org",
            slug="org",
            owner_user=authenticated_user,
        )
        project = Project.objects.create(
            organization=org,
            name="Test",
            created_by_user=authenticated_user,
        )
        
        ProjectMember.objects.filter(project=project, user=authenticated_user).delete()
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        client = APIClient()
        refresh = RefreshToken.for_user(another_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        response = client.delete(
            f"/api/v1/projects/{project.id}/",
            HTTP_X_ORGANIZATION_ID=str(org.id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.negative
    def test_update_project_invalid_status(self, authenticated_client, project):
        """Test that updating with invalid status is rejected."""
        response = authenticated_client.patch(
            f"/api/v1/projects/{project.id}/",
            {
                "status": "invalid",
            },
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.auth
    def test_project_detail_requires_authentication(self, api_client, project):
        """Test that authentication is required."""
        response = api_client.get(
            f"/api/v1/projects/{project.id}/",
            HTTP_X_ORGANIZATION_ID=str(project.organization.id),
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


