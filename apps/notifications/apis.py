from uuid import UUID

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from django.core.paginator import EmptyPage, Paginator
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

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
from apps.core.exceptions import OrgAccessDeniedException, ResourceConflictException, ResourceNotFoundException
from apps.core.permissions import HasOrganizationContext
from apps.notifications.models import Notification
from apps.tasks.services import TaskService


def _fmt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def _payload(n: Notification, updated_by=None):
    actor = updated_by or "system"
    return {
        "id": str(n.id),
        "recipient_user_id": str(n.recipient_user_id),
        "organization_id": str(n.organization_id),
        "type": n.type,
        "title": n.title,
        "body": n.body,
        "payload_json": n.payload_json,
        "is_read": n.is_read,
        "created_at": _fmt(n.created_at),
        "read_at": _fmt(n.read_at),
        "updated_at": _fmt(n.read_at or n.created_at),
        "created_by": "system",
        "updated_by": str(actor),
    }


def _project(data: dict, fields_param: str | None):
    if not fields_param or fields_param == "all":
        return data
    fields = {f.strip() for f in fields_param.split(",") if f.strip()}
    return {k: v for k, v in data.items() if k in fields}


class NotificationPayloadSerializer(serializers.Serializer):
    id = serializers.CharField()
    recipient_user_id = serializers.CharField()
    organization_id = serializers.CharField()
    type = serializers.CharField()
    title = serializers.CharField()
    body = serializers.CharField()
    payload_json = serializers.JSONField()
    is_read = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    read_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField()
    created_by = serializers.CharField()
    updated_by = serializers.CharField()


class NotificationReadRequestSerializer(serializers.Serializer):
    is_read = serializers.BooleanField(help_text="Must be true.")


NotificationListResponseSerializer = paginated_response_serializer("NotificationListResponse", NotificationPayloadSerializer)
NotificationResponseSerializer = success_response_serializer("NotificationResponse", NotificationPayloadSerializer)
NOTIFICATION_ID_PARAMETER = uuid_path_parameter("id", "Notification UUID.")
NOTIFICATION_IS_READ_PARAMETER = OpenApiParameter(
    name="is_read",
    type=OpenApiTypes.BOOL,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Filter by read state.",
)
NOTIFICATION_TYPE_PARAMETER = OpenApiParameter(
    name="type",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Filter by notification type.",
)


@extend_schema_view(
    get=extend_schema(
        operation_id="notifications_list",
        summary="List current user's notifications",
        parameters=[ORG_HEADER_PARAMETER, SEARCH_PARAMETER, NOTIFICATION_IS_READ_PARAMETER, NOTIFICATION_TYPE_PARAMETER, sort_parameter("created_at", "is_read"), ORDER_PARAMETER, PAGE_PARAMETER, LIMIT_PARAMETER, FIELDS_PARAMETER],
        responses={200: NotificationListResponseSerializer},
    )
)
class NotificationsListApi(APIView):
    permission_classes = [HasOrganizationContext]
    ALLOWED_SORT = {"created_at", "is_read"}

    def get(self, request):
        org = TaskService.get_org_or_404(request.headers.get("X-Organization-ID"))
        role = TaskService.require_role(request.user, org, TaskService.READ_ROLES)
        if role not in {"super_admin", "organization_admin", "project_manager", "team_member", "viewer"}:
            raise OrgAccessDeniedException(
                "You do not have permission to access notifications in this organization.",
                extra_details={"organization_id": str(org.id)},
            )

        qs = Notification.objects.filter(organization=org, recipient_user=request.user)

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(title__icontains=search) | qs.filter(body__icontains=search)

        is_read = request.query_params.get("is_read")
        if is_read is not None:
            if is_read.lower() not in {"true", "false"}:
                from rest_framework.exceptions import ValidationError

                raise ValidationError({"is_read": ["Must be true or false."]})
            qs = qs.filter(is_read=(is_read.lower() == "true"))

        notif_type = request.query_params.get("type")
        if notif_type:
            qs = qs.filter(type=notif_type)

        sort_by = request.query_params.get("sort_by", "created_at")
        if sort_by not in self.ALLOWED_SORT:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"sort_by": ["Invalid sort field."]})
        order = request.query_params.get("order", "desc")
        if order not in {"asc", "desc"}:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"order": ["Order must be asc or desc."]})
        qs = qs.order_by(sort_by if order == "asc" else f"-{sort_by}")

        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 20))
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
        items = [_project(_payload(n), fields_param) for n in page_obj.object_list]
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
                "message": "Notifications retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    patch=extend_schema(
        operation_id="notifications_mark_read",
        summary="Mark a notification as read",
        parameters=[ORG_HEADER_PARAMETER, NOTIFICATION_ID_PARAMETER],
        request=NotificationReadRequestSerializer,
        responses={200: success_response_serializer(
            "NotificationMarkReadResponse",
            inline_serializer(
                name="NotificationMarkReadData",
                fields={
                    "id": serializers.CharField(),
                    "recipient_user_id": serializers.CharField(),
                    "organization_id": serializers.CharField(),
                    "is_read": serializers.BooleanField(),
                    "read_at": serializers.DateTimeField(),
                    "updated_at": serializers.DateTimeField(),
                    "updated_by": serializers.CharField(),
                    "created_at": serializers.DateTimeField(),
                    "created_by": serializers.CharField(),
                }
            ),
        )},
    )
)
class NotificationMarkAsReadApi(APIView):
    permission_classes = [HasOrganizationContext]
    serializer_class = NotificationReadRequestSerializer

    def patch(self, request, id):
        org = TaskService.get_org_or_404(request.headers.get("X-Organization-ID"))
        try:
            UUID(str(id))
        except ValueError as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"id": ["Must be a valid UUID."]}) from exc

        try:
            notification = Notification.objects.get(id=id, organization=org, recipient_user=request.user)
        except Notification.DoesNotExist as exc:
            raise ResourceNotFoundException(
                "Organization/notification not found or deleted.",
                extra_details={"notification_id": str(id), "organization_id": str(org.id)},
            ) from exc

        if request.data.get("is_read") is not True:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"is_read": ["Must be true."]})

        if notification.is_read:
            raise ResourceConflictException(
                "This notification is already marked as read.",
                extra_details={"notification_id": str(notification.id), "is_read": True},
            )

        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])
        data = {
            "id": str(notification.id),
            "recipient_user_id": str(notification.recipient_user_id),
            "organization_id": str(notification.organization_id),
            "is_read": notification.is_read,
            "read_at": _fmt(notification.read_at),
            "updated_at": _fmt(notification.read_at),
            "updated_by": str(request.user.id),
            "created_at": _fmt(notification.created_at),
            "created_by": "system",
        }
        return Response(
            {"success": True, "data": data, "message": "Notification marked as read successfully."},
            status=status.HTTP_200_OK,
        )
