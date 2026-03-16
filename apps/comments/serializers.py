from rest_framework import serializers
import html

from apps.comments.models import Comment


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("body", "parent_comment_id")

    def validate_body(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        if len(value) > 5000:
            raise serializers.ValidationError("Comment body must not exceed 5000 characters.")
        
        # Basic script tag detection
        dangerous_patterns = ["<script", "<iframe", "javascript:", "onerror=", "onload="]
        if any(pattern in value.lower() for pattern in dangerous_patterns):
            raise serializers.ValidationError("Comment contains disallowed HTML/script tags.")
        
        return value


class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("body",)

    def validate_body(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        if len(value) > 5000:
            raise serializers.ValidationError("Comment body must not exceed 5000 characters.")
        
        dangerous_patterns = ["<script", "<iframe", "javascript:", "onerror=", "onload="]
        if any(pattern in value.lower() for pattern in dangerous_patterns):
            raise serializers.ValidationError("Comment contains disallowed HTML/script tags.")
        
        return value


class CommentResponseSerializer(serializers.ModelSerializer):
    author_user_id = serializers.CharField(source="author_user.id", read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "task_id",
            "author_user_id",
            "parent_comment_id",
            "body",
            "is_edited",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "author_user_id", "created_at", "updated_at")
