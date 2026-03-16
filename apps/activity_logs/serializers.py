from rest_framework import serializers

from apps.activity_logs.models import ActivityLog


class ActivityLogResponseSerializer(serializers.ModelSerializer):
    actor_user_id = serializers.CharField(source="actor_user.id", read_only=True)
    organization_id = serializers.CharField(source="organization.id", read_only=True)
    metadata = serializers.CharField(source="metadata_json", read_only=True)

    class Meta:
        model = ActivityLog
        fields = (
            "id",
            "organization_id",
            "actor_user_id",
            "event_type",
            "target_type",
            "target_id",
            "metadata",
            "created_at",
        )
        read_only_fields = ("id", "created_at")
