from rest_framework import serializers

from apps.users.models import User


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=12)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name")

    def validate_password(self, value):
        """Validate password complexity: uppercase, lowercase, digit, symbol."""
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError("Must include uppercase letter.")
        if not any(c.islower() for c in value):
            raise serializers.ValidationError("Must include lowercase letter.")
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("Must include digit.")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in value):
            raise serializers.ValidationError("Must include symbol.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class AuthTokenResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    expires_in = serializers.IntegerField()
    token_type = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "is_email_verified", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at", "is_email_verified")


class UserUpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name")

    def validate_first_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Ensure this field has at least 2 characters.")
        return value

    def validate_last_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Ensure this field has at least 2 characters.")
        return value


class EmailVerificationRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class EmailVerificationConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=12)

    def validate_new_password(self, value):
        """Validate password complexity."""
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError("Must include uppercase letter.")
        if not any(c.islower() for c in value):
            raise serializers.ValidationError("Must include lowercase letter.")
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("Must include digit.")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in value):
            raise serializers.ValidationError("Must include symbol.")
        return value


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
