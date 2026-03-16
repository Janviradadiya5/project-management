from rest_framework import serializers
from django.utils import timezone

from apps.tasks.models import Task


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("project_id", "title", "description", "priority", "status", "due_at", "assignee_user_id")

    def validate_title(self, value):
        if not value or len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters.")
        if len(value) > 300:
            raise serializers.ValidationError("Title must not exceed 300 characters.")
        dangerous_patterns = ["<script", "<iframe", "javascript:", "onclick"]
        if any(pattern in value.lower() for pattern in dangerous_patterns):
            raise serializers.ValidationError("Title contains invalid characters.")
        return value

    def validate_description(self, value):
        if value and len(value) > 5000:
            raise serializers.ValidationError("Description must not exceed 5000 characters.")
        if value:
            dangerous_patterns = ["<script", "<iframe"]
            if any(pattern in value.lower() for pattern in dangerous_patterns):
                raise serializers.ValidationError("Description contains unsafe HTML.")
        return value

    def validate_priority(self, value):
        valid_priorities = [Task.PRIORITY_LOW, Task.PRIORITY_MEDIUM, Task.PRIORITY_HIGH]
        if value not in valid_priorities:
            raise serializers.ValidationError(f"Priority must be one of {valid_priorities}.")
        return value

    def validate_status(self, value):
        valid_statuses = [Task.STATUS_TODO, Task.STATUS_IN_PROGRESS, Task.STATUS_DONE]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of {valid_statuses}.")
        return value

    def validate_due_at(self, value):
        if value and value < timezone.now():
            raise serializers.ValidationError("Due date must be in the future.")
        return value


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("title", "description", "priority", "status", "due_at", "assignee_user_id")

    def validate_title(self, value):
        if value and len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters.")
        if value and len(value) > 300:
            raise serializers.ValidationError("Title must not exceed 300 characters.")
        dangerous_patterns = ["<script", "<iframe", "javascript:", "onclick"]
        if value and any(pattern in value.lower() for pattern in dangerous_patterns):
            raise serializers.ValidationError("Title contains invalid characters.")
        return value

    def validate_description(self, value):
        if value and len(value) > 5000:
            raise serializers.ValidationError("Description must not exceed 5000 characters.")
        if value:
            dangerous_patterns = ["<script", "<iframe"]
            if any(pattern in value.lower() for pattern in dangerous_patterns):
                raise serializers.ValidationError("Description contains unsafe HTML.")
        return value

    def validate_priority(self, value):
        if value:
            valid_priorities = [Task.PRIORITY_LOW, Task.PRIORITY_MEDIUM, Task.PRIORITY_HIGH]
            if value not in valid_priorities:
                raise serializers.ValidationError(f"Priority must be one of {valid_priorities}.")
        return value

    def validate_status(self, value):
        if value:
            valid_statuses = [Task.STATUS_TODO, Task.STATUS_IN_PROGRESS, Task.STATUS_DONE]
            if value not in valid_statuses:
                raise serializers.ValidationError(f"Status must be one of {valid_statuses}.")
        return value

    def validate_due_at(self, value):
        if value and value < timezone.now():
            raise serializers.ValidationError("Due date must be in the future.")
        return value


class TaskResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            "id",
            "project_id",
            "title",
            "description",
            "priority",
            "status",
            "due_at",
            "assignee_user_id",
            "completed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "completed_at", "created_at", "updated_at")
