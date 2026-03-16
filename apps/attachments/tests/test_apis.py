"""Tests for Attachment REST API endpoints."""

import pytest
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.attachments.models import Attachment
from apps.projects.models import ProjectMember


@pytest.mark.django_db
class TestAttachmentUploadApi:
    """Test cases for Attachment upload endpoint."""

    @pytest.mark.auth
    def test_upload_attachment_authentication_required(self, api_client, task):
        """Test that authentication is required."""
        response = api_client.post(
            f"/api/v1/tasks/{task.id}/attachment/upload/",
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_attachment_success(self, authenticated_client, task):
        """Test successfully uploading an attachment."""
        file = SimpleUploadedFile(
            name="test.pdf",
            content=b"PDF content",
            content_type="application/pdf",
        )
        
        response = authenticated_client.post(
            f"/api/v1/tasks/{task.id}/attachment/upload/",
            {"file": file},
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
            format="multipart",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["file_name"] == "test.pdf"

    @pytest.mark.negative
    def test_upload_attachment_invalid_mime_type(self, authenticated_client, task):
        """Test that invalid MIME types are rejected."""
        file = SimpleUploadedFile(
            name="malware.exe",
            content=b"MZ",  # Windows executable header
            content_type="application/octet-stream",
        )
        
        response = authenticated_client.post(
            f"/api/v1/tasks/{task.id}/attachment/upload/",
            {"file": file},
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.negative
    def test_upload_attachment_file_too_large(self, authenticated_client, task):
        """Test that oversized files are rejected."""
        # Create a file larger than 25MB
        large_content = b"x" * (Attachment.MAX_SIZE_BYTES + 1)
        file = SimpleUploadedFile(
            name="huge.pdf",
            content=large_content,
            content_type="application/pdf",
        )
        
        response = authenticated_client.post(
            f"/api/v1/tasks/{task.id}/attachment/upload/",
            {"file": file},
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.permission
    def test_upload_attachment_permission_denied(self, authenticated_user, another_user):
        """Test that non-members cannot upload."""
        from apps.projects.models import Project
        from apps.tasks.models import Task
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
            title="Test Task",
            created_by_user=authenticated_user,
        )
        
        file = SimpleUploadedFile(
            name="test.pdf",
            content=b"PDF",
            content_type="application/pdf",
        )
        
        client = APIClient()
        refresh = RefreshToken.for_user(another_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        response = client.post(
            f"/api/v1/tasks/{task.id}/attachment/upload/",
            {"file": file},
            HTTP_X_ORGANIZATION_ID=str(org.id),
            format="multipart",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAttachmentDetailApi:
    """Test cases for Attachment detail endpoint."""

    def test_get_attachment_success(self, authenticated_client, attachment):
        """Test successfully retrieving attachment."""
        response = authenticated_client.get(
            f"/api/v1/attachment/{attachment.id}/",
            HTTP_X_ORGANIZATION_ID=str(attachment.task.project.organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["file_name"] == attachment.file_name

    @pytest.mark.negative
    def test_get_attachment_not_found(self, authenticated_client, organization):
        """Test getting non-existent attachment."""
        import uuid
        response = authenticated_client.get(
            f"/api/v1/attachment/{uuid.uuid4()}/",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.permission
    def test_get_attachment_permission_denied(self, authenticated_user, another_user):
        """Test that non-members cannot access."""
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        client = APIClient()
        refresh = RefreshToken.for_user(another_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        from apps.projects.models import Project, ProjectMember
        from apps.tasks.models import Task
        from apps.attachments.models import Attachment
        from apps.organizations.models import Organization
        
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
            title="Test Task",
            created_by_user=authenticated_user,
        )
        attachment = Attachment.objects.create(
            task=task,
            uploaded_by_user=authenticated_user,
            file_name="secret.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            storage_key="s3://bucket/secret.pdf",
            checksum="hash123",
        )
        
        response = client.get(
            f"/api/v1/attachment/{attachment.id}/",
            HTTP_X_ORGANIZATION_ID=str(org.id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_attachment_success(self, authenticated_client, attachment):
        """Test successfully deleting attachment."""
        attachment_id = attachment.id
        response = authenticated_client.delete(
            f"/api/v1/attachment/{attachment_id}/",
            HTTP_X_ORGANIZATION_ID=str(attachment.task.project.organization.id),
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]
        assert not Attachment.objects.filter(id=attachment_id).exists()

    @pytest.mark.permission
    def test_delete_attachment_not_owner_or_manager(self, authenticated_user, another_user):
        """Test that only owner/manager can delete."""
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        from apps.projects.models import Project, ProjectMember
        from apps.tasks.models import Task
        from apps.attachments.models import Attachment
        from apps.organizations.models import Organization
        
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
            title="Test Task",
            created_by_user=authenticated_user,
        )
        attachment = Attachment.objects.create(
            task=task,
            uploaded_by_user=authenticated_user,
            file_name="owned.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            storage_key="s3://bucket/owned.pdf",
            checksum="hash123",
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
            f"/api/v1/attachment/{attachment.id}/",
            HTTP_X_ORGANIZATION_ID=str(org.id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

