import uuid

from django.db import models
from django.contrib.postgres.indexes import GinIndex

from apps.organizations.models import Organization
from apps.users.models import User


class ActivityLog(models.Model):
    """Append-only audit log. Never update or delete rows."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.RESTRICT,
        related_name="activity_logs",
    )
    actor_user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="activity_logs",
    )
    event_type = models.CharField(max_length=80)
    target_type = models.CharField(max_length=80)
    target_id = models.UUIDField()
    metadata_json = models.JSONField(default=dict)
    request_id = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "activity_logs"
        indexes = [
            models.Index(
                fields=["organization", "created_at"],
                name="idx_actlog_org_created",
            ),
            models.Index(
                fields=["actor_user", "created_at"],
                name="idx_actlog_actor_created",
            ),
            models.Index(fields=["event_type"], name="idx_activity_logs_event_type"),
            GinIndex(fields=["metadata_json"], name="idx_activity_logs_metadata_gin"),
        ]

    def __str__(self):
        return f"ActivityLog({self.event_type}, org={self.organization_id})"

