from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationResponseSerializer(serializers.ModelSerializer):
    payload = serializers.CharField(source="payload_json", read_only=True)

    class Meta:
        model = Notification
        fields = ("id", "type", "title", "body", "payload", "is_read", "created_at", "read_at")
        read_only_fields = ("id", "type", "title", "body", "payload", "created_at")
