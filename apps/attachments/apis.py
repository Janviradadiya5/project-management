from drf_spectacular.utils import extend_schema, extend_schema_view
from django.core.paginator import EmptyPage, Paginator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename
from django.utils import timezone
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
import hashlib
from uuid import uuid4

from apps.core.openapi import (
    FIELDS_PARAMETER,
    LIMIT_PARAMETER,
    ORDER_PARAMETER,
    ORG_HEADER_PARAMETER,
    PAGE_PARAMETER,
    SEARCH_PARAMETER,
    paginated_response_serializer,
    sort_parameter,
    success_response_serializer,
    uuid_path_parameter,
)
from apps.attachments.models import Attachment
from apps.attachments.serializers import AttachmentUploadSerializer
from apps.attachments.services import AttachmentService
from apps.core.exceptions import ResourceConflictException
from apps.core.permissions import HasOrganizationContext
from apps.tasks.services import TaskService


def _fmt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def _display_name(user):
    if not user:
        return None
    full_name = f"{user.first_name} {user.last_name}".strip()
    return full_name or user.email


def _attachment_payload(a: Attachment, updated_by=None):
    actor = updated_by or a.uploaded_by_user_id
    return {
        "id": str(a.id),
        "task_id": str(a.task_id),
        "uploaded_by_user_id": str(a.uploaded_by_user_id),
        "uploaded_by_user_name": _display_name(getattr(a, "uploaded_by_user", None)),
        "file_name": a.file_name,
        "content_type": a.content_type,
        "size_bytes": a.size_bytes,
        "storage_key": a.storage_key,
        "checksum": a.checksum,
        "deleted_at": _fmt(a.deleted_at),
        "created_at": _fmt(a.created_at),
        "updated_at": _fmt(a.created_at),
        "created_by": str(a.uploaded_by_user_id),
        "updated_by": str(actor),
    }


def _apply_projection(data: dict, fields_param: str | None):
    if not fields_param or fields_param == "all":
        return data
    fields = {f.strip() for f in fields_param.split(",") if f.strip()}
    return {k: v for k, v in data.items() if k in fields}


class AttachmentPayloadSerializer(serializers.Serializer):
    id = serializers.CharField()
    task_id = serializers.CharField()
    uploaded_by_user_id = serializers.CharField()
    uploaded_by_user_name = serializers.CharField(allow_null=True, required=False)
    file_name = serializers.CharField()
    content_type = serializers.CharField()
    size_bytes = serializers.IntegerField()
    storage_key = serializers.CharField()
    checksum = serializers.CharField()
    deleted_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    created_by = serializers.CharField()
    updated_by = serializers.CharField()


AttachmentListResponseSerializer = paginated_response_serializer("AttachmentListResponse", AttachmentPayloadSerializer)
AttachmentResponseSerializer = success_response_serializer("AttachmentResponse", AttachmentPayloadSerializer)
TASK_ID_PARAMETER = uuid_path_parameter("task_id", "Task UUID.")
ATTACHMENT_ID_PARAMETER = uuid_path_parameter("id", "Attachment UUID.")


@extend_schema_view(
    post=extend_schema(
        operation_id="tasks_attachments_create",
        summary="Upload an attachment to a task",
        parameters=[ORG_HEADER_PARAMETER, TASK_ID_PARAMETER],
        request=AttachmentUploadSerializer,
        responses={201: AttachmentResponseSerializer},
    ),
    get=extend_schema(
        operation_id="tasks_attachments_list",
        summary="List task attachments",
        parameters=[ORG_HEADER_PARAMETER, TASK_ID_PARAMETER, SEARCH_PARAMETER, FIELDS_PARAMETER, sort_parameter("file_name", "size_bytes", "created_at"), ORDER_PARAMETER, PAGE_PARAMETER, LIMIT_PARAMETER],
        responses={200: AttachmentListResponseSerializer},
    ),
)
class AttachmentUploadApi(APIView):
    permission_classes = [HasOrganizationContext]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    ALLOWED_SORT = {"file_name", "size_bytes", "created_at"}
    serializer_class = AttachmentUploadSerializer

    def post(self, request, task_id):
        org = TaskService.get_org_or_404(request.headers.get("X-Organization-ID"))
        task = AttachmentService.get_task_or_404(task_id, org)
        AttachmentService.ensure_can_upload(request.user, task)

        serializer = AttachmentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = serializer.validated_data.get("file")
        storage_key = serializer.validated_data["storage_key"]
        checksum = serializer.validated_data["checksum"]

        if file_obj:
            raw_bytes = file_obj.read()
            checksum = hashlib.sha256(raw_bytes).hexdigest()
            safe_name = get_valid_filename(file_obj.name or "attachment.bin")
            storage_key = f"attachments/{task.id}/{uuid4().hex}-{safe_name}"
            default_storage.save(storage_key, ContentFile(raw_bytes))

        attachment = Attachment.objects.create(
            task=task,
            uploaded_by_user=request.user,
            file_name=serializer.validated_data["file_name"],
            content_type=serializer.validated_data["content_type"],
            size_bytes=serializer.validated_data["size_bytes"],
            storage_key=storage_key,
            checksum=checksum,
        )
        return Response(
            {"success": True, "data": _attachment_payload(attachment), "message": "Attachment uploaded successfully."},
            status=status.HTTP_201_CREATED,
        )

    def get(self, request, task_id):
        org = TaskService.get_org_or_404(request.headers.get("X-Organization-ID"))
        task = AttachmentService.get_task_or_404(task_id, org)
        AttachmentService.ensure_can_view(request.user, task)

        qs = Attachment.objects.filter(task=task)

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(file_name__icontains=search)

        content_type = request.query_params.get("content_type")
        if content_type:
            qs = qs.filter(content_type=content_type)

        sort_by = request.query_params.get("sort_by", "created_at")
        if sort_by not in self.ALLOWED_SORT:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"sort_by": ["Invalid sort field."]})
        order = request.query_params.get("order", "desc")
        if order not in {"asc", "desc"}:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"order": ["Order must be asc or desc."]})
        qs = qs.order_by(sort_by if order == "asc" else f"-{sort_by}")

        try:
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 20))
        except (TypeError, ValueError) as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"page": ["Must be an integer."], "limit": ["Must be an integer."]}) from exc
        if page < 1 or not (1 <= limit <= 100):
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"limit": ["Limit must be between 1 and 100."]})

        paginator = Paginator(qs, limit)
        try:
            page_obj = paginator.page(page)
        except EmptyPage as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"page": ["Requested page is out of range."]}) from exc

        fields_param = request.query_params.get("fields")
        items = [_apply_projection(_attachment_payload(a), fields_param) for a in page_obj.object_list]
        return Response(
            {
                "success": True,
                "data": {
                    "items": items,
                    "pagination": {
                        "page": page_obj.number,
                        "limit": limit,
                        "total_items": paginator.count,
                        "total_pages": paginator.num_pages,
                        "has_next": page_obj.has_next(),
                        "has_prev": page_obj.has_previous(),
                    },
                },
                "message": "Attachments retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    delete=extend_schema(
        operation_id="attachments_delete",
        summary="Soft-delete an attachment",
        parameters=[ORG_HEADER_PARAMETER, ATTACHMENT_ID_PARAMETER],
        responses={200: AttachmentResponseSerializer},
    )
)
class AttachmentDetailApi(APIView):
    permission_classes = [HasOrganizationContext]

    def delete(self, request, id):
        org = TaskService.get_org_or_404(request.headers.get("X-Organization-ID"))
        attachment = AttachmentService.get_attachment_or_404(id, org)
        AttachmentService.ensure_can_delete(request.user, attachment)
        if attachment.deleted_at:
            raise ResourceConflictException(
                "This attachment has already been deleted.",
                extra_details={"attachment_id": str(attachment.id), "current_state": "deleted"},
            )
        attachment.deleted_at = timezone.now()
        attachment.save(update_fields=["deleted_at"])
        data = _attachment_payload(attachment, updated_by=request.user.id)
        data["file_name"] = attachment.file_name
        return Response(
            {"success": True, "data": data, "message": "Attachment soft-deleted successfully."},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    delete=extend_schema(exclude=True)
)
class AttachmentDeleteApi(APIView):
    permission_classes = [HasOrganizationContext]

    def delete(self, request, id):
        return AttachmentDetailApi().delete(request, id)
