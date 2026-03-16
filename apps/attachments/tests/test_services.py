"""Tests for Attachment service business logic."""

import pytest

from apps.attachments.services import AttachmentService
from apps.projects.models import ProjectMember


@pytest.mark.django_db
class TestAttachmentService:
    """Test cases for AttachmentService methods."""

    @pytest.mark.permission
    def test_can_upload_attachment_as_member(self, task, authenticated_user):
        """Test that project members can upload attachments."""
        assert ProjectMember.objects.filter(
            user=authenticated_user,
            project=task.project,
        ).exists()
        assert AttachmentService.can_upload_attachment(authenticated_user, task) is True

    @pytest.mark.permission
    def test_cannot_upload_attachment_not_member(self, task, another_user):
        """Test that non-members cannot upload."""
        assert AttachmentService.can_upload_attachment(another_user, task) is False

    @pytest.mark.permission
    def test_can_access_attachment_as_member(self, attachment, authenticated_user):
        """Test that project members can access attachments."""
        assert AttachmentService.can_access_attachment(authenticated_user, attachment) is True

    @pytest.mark.permission
    def test_cannot_access_attachment_not_member(self, attachment, another_user):
        """Test that non-members cannot access."""
        assert AttachmentService.can_access_attachment(another_user, attachment) is False

    @pytest.mark.permission
    def test_can_delete_attachment_as_uploader(self, attachment, authenticated_user):
        """Test that uploader can delete attachment."""
        assert AttachmentService.can_delete_attachment(authenticated_user, attachment) is True

    @pytest.mark.permission
    def test_can_delete_attachment_as_manager(self, attachment, authenticated_user, another_user):
        """Test that project manager can delete attachment."""
        ProjectMember.objects.create(
            project=attachment.task.project,
            user=another_user,
            project_role=ProjectMember.ROLE_MANAGER,
            added_by_user=authenticated_user,
        )
        assert AttachmentService.can_delete_attachment(another_user, attachment) is True

    @pytest.mark.permission
    def test_cannot_delete_attachment_not_uploader_or_manager(self, attachment, authenticated_user, another_user):
        """Test that non-uploader/manager cannot delete."""
        ProjectMember.objects.create(
            project=attachment.task.project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        assert AttachmentService.can_delete_attachment(another_user, attachment) is False

    def test_create_attachment(self, task, authenticated_user):
        """Test creating an attachment from file."""
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file = SimpleUploadedFile(
            name="test.pdf",
            content=b"PDF content",
            content_type="application/pdf",
        )
        
        attachment = AttachmentService.create_attachment(task, file, authenticated_user)
        assert attachment.file_name == "test.pdf"
        assert attachment.uploaded_by_user == authenticated_user
        assert attachment.task == task
        assert attachment.checksum is not None

    def test_service_uses_real_queries(self, task, authenticated_user, another_user):
        """Test that service uses real database queries."""
        # Initially cannot upload
        assert AttachmentService.can_upload_attachment(another_user, task) is False
        
        # Add as member
        ProjectMember.objects.create(
            project=task.project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        
        # Now can upload
        assert AttachmentService.can_upload_attachment(another_user, task) is True

