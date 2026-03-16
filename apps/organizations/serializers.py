from rest_framework import serializers
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import Role, User


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("name", "slug")

    def validate_name(self, value):
        if not value or len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters.")
        if len(value) > 120:
            raise serializers.ValidationError("Name must not exceed 120 characters.")
        # HTML/script injection prevention
        dangerous_patterns = ["<script", "<iframe", "javascript:", "onclick"]
        if any(pattern in value.lower() for pattern in dangerous_patterns):
            raise serializers.ValidationError("Name contains invalid characters.")
        return value

    def validate_slug(self, value):
        if not value:
            raise serializers.ValidationError("Slug is required.")
        slug_validator = RegexValidator(
            regex=r'^[a-z0-9]+(?:-[a-z0-9]+)*$',
            message='Slug must contain only lowercase letters, numbers, and hyphens.'
        )
        try:
            slug_validator(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message)
        return value


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("name", "slug", "status")

    def validate_status(self, value):
        if value not in [Organization.STATUS_ACTIVE, Organization.STATUS_ARCHIVED]:
            raise serializers.ValidationError("Invalid status.")
        return value

    def validate_name(self, value):
        if value and len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters.")
        if value and len(value) > 120:
            raise serializers.ValidationError("Name must not exceed 120 characters.")
        dangerous_patterns = ["<script", "<iframe", "javascript:", "onclick"]
        if value and any(pattern in value.lower() for pattern in dangerous_patterns):
            raise serializers.ValidationError("Name contains invalid characters.")
        return value

    def validate_slug(self, value):
        if value:
            slug_validator = RegexValidator(
                regex=r'^[a-z0-9]+(?:-[a-z0-9]+)*$',
                message='Slug must contain only lowercase letters, numbers, and hyphens.'
            )
            try:
                slug_validator(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(e.message)
        return value


class OrganizationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "status", "deleted_at", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class InviteMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role_id = serializers.UUIDField(required=False)
    role_code = serializers.CharField(required=False)

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required.")
        if len(value) > 255:
            raise serializers.ValidationError("Email must not exceed 255 characters.")
        return value.lower()

    def validate_role_id(self, value):
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid role_id: role does not exist.")
        return value

    def validate_role_code(self, value):
        normalized = str(value or "").strip().lower()
        if not normalized:
            raise serializers.ValidationError("role_code cannot be empty.")
        if not Role.objects.filter(code=normalized).exists():
            raise serializers.ValidationError("Invalid role_code: role does not exist.")
        return normalized

    def validate(self, data):
        role_id = data.get("role_id")
        role_code = data.get("role_code")

        if not role_id and not role_code:
            raise serializers.ValidationError("Either role_id or role_code must be provided.")

        if role_code:
            role = Role.objects.get(code=role_code)
            if role_id and role.id != role_id:
                raise serializers.ValidationError("role_id and role_code do not match.")
            data["role_id"] = role.id

        return data


class AcceptInviteSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Token is required.")
        if len(value) > 500:
            raise serializers.ValidationError("Invalid token format.")
        return value


class OrganizationMembershipResponseSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationMembership
        fields = ("id", "user", "role", "status", "joined_at", "created_at")
        read_only_fields = ("id", "created_at")

    def get_user(self, obj):
        return {
            "id": str(obj.user.id),
            "email": obj.user.email,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
        }

    def get_role(self, obj):
        return {"code": obj.role.code, "name": obj.role.name}


class UpdateMembershipSerializer(serializers.Serializer):
    role_id = serializers.UUIDField(required=False)
    role_code = serializers.CharField(max_length=100, required=False)
    status = serializers.CharField(max_length=20, required=False)

    def validate_role_id(self, value):
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid role_id: role does not exist.")
        return value

    def validate_status(self, value):
        allowed = ["active", "suspended"]
        if value not in allowed:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(allowed)}.")
        return value

    def validate_role_code(self, value):
        normalized = str(value or "").strip().lower()
        if not normalized:
            raise serializers.ValidationError("role_code cannot be empty.")
        if not Role.objects.filter(code=normalized).exists():
            raise serializers.ValidationError("Invalid role_code: role does not exist.")
        return normalized

    def validate(self, data):
        role_id = data.get("role_id")
        role_code = data.get("role_code")

        if role_code:
            role = Role.objects.get(code=role_code)
            if role_id and role.id != role_id:
                raise serializers.ValidationError("role_id and role_code do not match.")
            data["role_id"] = role.id

        if not data.get("role_id") and not data.get("status"):
            raise serializers.ValidationError("At least one of role_id, role_code, or status must be provided.")
        return data

