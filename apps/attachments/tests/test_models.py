"""Tests for Attachment model."""

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.attachments.models import Attachment


@pytest.mark.django_db
class TestAttachmentModel:
    """Test cases for Attachment model."""

    def test_create_attachment_with_valid_data(self, task, authenticated_user):
        """Test creating an attachment with valid data."""
        attachment = Attachment.objects.create(
            task=task,
            uploaded_by_user=authenticated_user,
            file_name="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            storage_key="s3://bucket/test.pdf",
            checksum="abc123",
        )
        assert attachment.id is not None
        assert attachment.task == task
        assert attachment.uploaded_by_user == authenticated_user
        assert attachment.file_name == "test.pdf"
        assert attachment.size_bytes == 1024
        assert attachment.deleted_at is None
        assert attachment.created_at is not None

    def test_attachment_string_representation(self, attachment):
        """Test __str__ method returns file name."""
        assert str(attachment) == "test.pdf"

    def test_attachment_created_at_auto_generated(self, task, authenticated_user):
        """Test that created_at is automatically set."""
        before = timezone.now()
        attachment = Attachment.objects.create(
            task=task,
            uploaded_by_user=authenticated_user,
            file_name="timestamp.pdf",
            content_type="application/pdf",
            size_bytes=2048,
            storage_key="s3://bucket/timestamp.pdf",
            checksum="def456",
        )
        after = timezone.now()
        assert before <= attachment.created_at <= after

    def test_attachment_soft_delete(self, attachment):
        """Test soft delete with deleted_at."""
        assert attachment.deleted_at is None
        delete_time = timezone.now()
        attachment.deleted_at = delete_time
        attachment.save()
        attachment.refresh_from_db()
        assert attachment.deleted_at == delete_time

    def test_attachment_max_size_constraint(self, task, authenticated_user):
        """Test that file size cannot exceed max."""
        max_size = Attachment.MAX_SIZE_BYTES + 1
        attachment = Attachment(
            task=task,
            uploaded_by_user=authenticated_user,
            file_name="toolarge.zip",
            content_type="application/zip",
            size_bytes=max_size,
            storage_key="s3://bucket/toolarge.zip",
            checksum="xyz789",
        )
        # Note: Constraint is enforced at DB level, so save will fail
        with pytest.raises(IntegrityError):
            attachment.save()

    def test_attachment_within_size_limit(self, task, authenticated_user):
        """Test that file within limit is accepted."""
        max_allowed = Attachment.MAX_SIZE_BYTES
        attachment = Attachment.objects.create(
            task=task,
            uploaded_by_user=authenticated_user,
            file_name="large.zip",
            content_type="application/zip",
            size_bytes=max_allowed,
            storage_key="s3://bucket/large.zip",
            checksum="hash123",
        )
        assert attachment.size_bytes == max_allowed

    def test_attachment_foreign_key_task_cascade(self, attachment):
        """Test that deleting task cascades to attachments."""
        attachment_id = attachment.id
        task = attachment.task
        task.delete()
        assert not Attachment.objects.filter(id=attachment_id).exists()

    def test_attachment_uploaded_by_restrict(self, attachment):
        """Test that deleting uploader is restricted."""
        with pytest.raises(IntegrityError):
            attachment.uploaded_by_user.delete()

    def test_attachment_checksum_storage(self, task, authenticated_user):
        """Test that checksum is properly stored."""
        checksum = "md5hash123456abcdef"
        attachment = Attachment.objects.create(
            task=task,
            uploaded_by_user=authenticated_user,
            file_name="checksumtest.pdf",
            content_type="application/pdf",
            size_bytes=5120,
            storage_key="s3://bucket/checksumtest.pdf",
            checksum=checksum,
        )
        attachment.refresh_from_db()
        assert attachment.checksum == checksum

    def test_attachment_storage_key_paths(self, task, authenticated_user):
        """Test various storage key formats."""
        storage_keys = [
            "s3://bucket/folder/file.pdf",
            "gcs://bucket/path/to/file.doc",
            "/local/path/file.txt",
        ]
        for i, key in enumerate(storage_keys):
            attachment = Attachment.objects.create(
                task=task,
                uploaded_by_user=authenticated_user,
                file_name=f"file{i}.pdf",
                content_type="application/pdf",
                size_bytes=1024,
                storage_key=key,
                checksum=f"hash{i}",
            )
            assert attachment.storage_key == key

    def test_attachment_multiple_per_task(self, task, authenticated_user):
        """Test multiple attachments for same task."""
        for i in range(3):
            Attachment.objects.create(
                task=task,
                uploaded_by_user=authenticated_user,
                file_name=f"file{i}.pdf",
                content_type="application/pdf",
                size_bytes=1024 * (i + 1),
                storage_key=f"s3://bucket/file{i}.pdf",
                checksum=f"hash{i}",
            )
        assert task.attachments.count() == 3

    def test_attachment_content_types(self, task, authenticated_user):
        """Test various MIME types."""
        mime_types = [
            "application/pdf",
            "image/jpeg",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        ]
        for i, mime_type in enumerate(mime_types):
            attachment = Attachment.objects.create(
                task=task,
                uploaded_by_user=authenticated_user,
                file_name=f"file{i}",
                content_type=mime_type,
                size_bytes=1024,
                storage_key=f"s3://bucket/file{i}",
                checksum=f"hash{i}",
            )
            assert attachment.content_type == mime_type

