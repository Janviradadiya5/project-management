import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.postgres.indexes import GinIndex

from apps.organizations.models import Organization
from apps.users.models import User


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    body = models.TextField()
    payload_json = models.JSONField(default=dict)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_notifications_audit",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_notifications_audit",
        db_column="updated_by",
    )

    class Meta:
        db_table = "notifications"
        indexes = [
            models.Index(
                fields=["recipient_user", "created_at"],
                name="idx_notif_recipient_created",
            ),
            models.Index(
                fields=["organization", "type"],
                name="idx_notifications_org_type",
            ),
            GinIndex(fields=["payload_json"], name="idx_notifications_payload_gin"),
        ]

    def __str__(self):
        return f"Notification({self.type}, user={self.recipient_user_id})"

    def clean(self):
        if self.is_read and not self.read_at:
            raise ValidationError(
                {"read_at": "read_at must be set when is_read is True."}
            )

