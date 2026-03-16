import uuid

from django.db import models

from apps.core.models import BaseModel
from apps.organizations.models import Organization


class WebhookEndpoint(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="webhook_endpoints",
    )
    url = models.CharField(max_length=500)
    secret_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "webhook_endpoints"
        indexes = [
            models.Index(fields=["organization"], name="idx_webhook_endpoints_org_id"),
        ]

    def __str__(self):
        return f"WebhookEndpoint({self.url[:60]})"


class WebhookDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook_endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    event_type = models.CharField(max_length=80)
    payload_json = models.JSONField()
    http_status = models.IntegerField(null=True, blank=True)
    attempt_count = models.IntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "webhook_deliveries"
        indexes = [
            models.Index(
                fields=["webhook_endpoint"],
                name="idx_webhookdel_endpoint",
            ),
        ]

    def __str__(self):
        return f"WebhookDelivery({self.event_type}, endpoint={self.webhook_endpoint_id})"

