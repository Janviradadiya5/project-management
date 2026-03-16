import uuid

from django.db import models

from apps.tasks.models import Task
from apps.users.models import User


class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by_user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="uploaded_attachments",
    )
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=150)
    size_bytes = models.BigIntegerField()
    storage_key = models.CharField(max_length=500)
    checksum = models.CharField(max_length=128)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_attachments_audit",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_attachments_audit",
        db_column="updated_by",
    )

    # 25 MB hard limit (25 * 1024 * 1024)
    MAX_SIZE_BYTES = 26_214_400

    class Meta:
        db_table = "attachments"
        indexes = [
            models.Index(fields=["task"], name="idx_attachments_task_id"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(size_bytes__lte=26_214_400),
                name="ck_attachments_size_bytes",
            ),
        ]

    def __str__(self):
        return self.file_name

