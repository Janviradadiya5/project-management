from rest_framework import serializers
from django.utils import timezone

from apps.core.exceptions import ProjectDeadlineInvalidException, ProjectStatusInvalidException
from apps.projects.models import Project, ProjectMember
from apps.users.models import User


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("name", "description", "status", "deadline_at")

    def validate_name(self, value):
        if not value or len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters.")
        if len(value) > 200:
            raise serializers.ValidationError("Name must not exceed 200 characters.")
        # Prevent HTML/script injection
        dangerous_patterns = ["<script", "<iframe", "javascript:", "onclick"]
        if any(pattern in value.lower() for pattern in dangerous_patterns):
            raise serializers.ValidationError("Name contains invalid characters.")
        return value

    def validate_description(self, value):
        if value and len(value) > 10000:
            raise serializers.ValidationError("Description must not exceed 10000 characters.")
        if value:
            dangerous_patterns = ["<script", "<iframe"]
            if any(pattern in value.lower() for pattern in dangerous_patterns):
                raise serializers.ValidationError("Description contains unsafe HTML.")
        return value

    def validate_status(self, value):
        if value not in [Project.STATUS_ACTIVE, Project.STATUS_COMPLETED, Project.STATUS_ARCHIVED]:
            raise ProjectStatusInvalidException(
                "Project status must be one of: active, completed, archived.",
                extra_details={"status": value},
            )
        return value

    def validate_deadline_at(self, value):
        if value and value < timezone.now():
            raise ProjectDeadlineInvalidException(
                "Project deadline must be greater than or equal to the creation time.",
                extra_details={"deadline_at": value.strftime("%Y-%m-%dT%H:%M:%SZ")},
            )
        return value


class ProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("name", "description", "status", "deadline_at")

    def validate_name(self, value):
        if value and len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters.")
        if value and len(value) > 200:
            raise serializers.ValidationError("Name must not exceed 200 characters.")
        dangerous_patterns = ["<script", "<iframe", "javascript:", "onclick"]
        if value and any(pattern in value.lower() for pattern in dangerous_patterns):
            raise serializers.ValidationError("Name contains invalid characters.")
        return value

    def validate_description(self, value):
        if value and len(value) > 10000:
            raise serializers.ValidationError("Description must not exceed 10000 characters.")
        if value:
            dangerous_patterns = ["<script", "<iframe"]
            if any(pattern in value.lower() for pattern in dangerous_patterns):
                raise serializers.ValidationError("Description contains unsafe HTML.")
        return value

    def validate_status(self, value):
        if value not in [Project.STATUS_ACTIVE, Project.STATUS_COMPLETED, Project.STATUS_ARCHIVED]:
            raise ProjectStatusInvalidException(
                "Project status must be one of: active, completed, archived.",
                extra_details={"status": value},
            )
        return value

    def validate_deadline_at(self, value):
        if value and value < timezone.now():
            raise ProjectDeadlineInvalidException(
                "Project deadline must be greater than or equal to the creation time.",
                extra_details={"deadline_at": value.strftime("%Y-%m-%dT%H:%M:%SZ")},
            )
        return value


class ProjectResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "organization_id", "name", "description", "status", "deadline_at", "created_at", "updated_at")
        read_only_fields = ("id", "organization_id", "created_at", "updated_at")


class ProjectMemberAddSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    project_role = serializers.CharField(default="contributor")

    def validate_project_role(self, value):
        if value not in [ProjectMember.ROLE_MANAGER, ProjectMember.ROLE_CONTRIBUTOR, ProjectMember.ROLE_VIEWER]:
            raise serializers.ValidationError("Invalid project role.")
        return value


class ProjectMemberResponseSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMember
        fields = ("id", "user", "project_role", "created_at")
        read_only_fields = ("id", "created_at")

    def get_user(self, obj):
        return {
            "id": str(obj.user.id),
            "email": obj.user.email,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
        }
