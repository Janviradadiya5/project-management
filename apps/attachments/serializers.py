from rest_framework import serializers

from apps.attachments.models import Attachment


class AttachmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)
    file_name = serializers.CharField(max_length=255, required=False)
    content_type = serializers.CharField(max_length=150, required=False)
    size_bytes = serializers.IntegerField(min_value=1, required=False)
    storage_key = serializers.CharField(max_length=500, required=False)
    checksum = serializers.CharField(max_length=128, required=False)

    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "text/plain",
    }

    def validate_content_type(self, value):
        if value not in self.ALLOWED_MIME_TYPES:
            from apps.core.exceptions import AttachmentTypeForbiddenException

            raise AttachmentTypeForbiddenException(
                f"Attachment content type '{value}' is not allowed.",
                extra_details={"content_type": value},
            )
        return value

    def validate_size_bytes(self, value):
        if value > Attachment.MAX_SIZE_BYTES:
            from apps.core.exceptions import AttachmentSizeExceededException

            raise AttachmentSizeExceededException(
                "Attachment exceeds the maximum allowed size of 25 MB.",
                extra_details={"size_bytes": value, "max_size_bytes": Attachment.MAX_SIZE_BYTES},
            )
        return value

    def validate_checksum(self, value):
        if not value.strip():
            raise serializers.ValidationError("Checksum is required.")
        return value.strip()

    def validate(self, attrs):
        file_obj = attrs.get("file")
        if file_obj:
            attrs.setdefault("file_name", getattr(file_obj, "name", "uploaded-file"))
            attrs.setdefault("content_type", getattr(file_obj, "content_type", "application/octet-stream"))
            attrs.setdefault("size_bytes", getattr(file_obj, "size", None))
            attrs.setdefault("storage_key", "pending")
            attrs.setdefault("checksum", "pending")

        required_without_file = ["file_name", "content_type", "size_bytes", "storage_key", "checksum"]
        missing = [key for key in required_without_file if not attrs.get(key)]

        if missing:
            raise serializers.ValidationError({field: ["This field is required."] for field in missing})

        if attrs.get("size_bytes"):
            self.validate_size_bytes(attrs["size_bytes"])
        if attrs.get("content_type"):
            self.validate_content_type(attrs["content_type"])
        if attrs.get("checksum"):
            attrs["checksum"] = self.validate_checksum(attrs["checksum"])

        return attrs


class AttachmentResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ("id", "task_id", "file_name", "content_type", "size_bytes", "storage_key", "checksum", "created_at")
        read_only_fields = ("id", "created_at")
