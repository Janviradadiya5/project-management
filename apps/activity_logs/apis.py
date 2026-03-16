from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from django.core.paginator import EmptyPage, Paginator
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
)
from apps.activity_logs.models import ActivityLog
from apps.core.exceptions import OrgAccessDeniedException
from apps.core.permissions import HasOrganizationContext
from apps.tasks.services import TaskService


def _fmt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def _payload(log: ActivityLog):
    return {
        "id": str(log.id),
        "organization_id": str(log.organization_id),
        "actor_user_id": str(log.actor_user_id),
        "event_type": log.event_type,
        "target_type": log.target_type,
        "target_id": str(log.target_id),
        "metadata_json": log.metadata_json,
        "request_id": str(log.request_id),
        "created_at": _fmt(log.created_at),
        "updated_at": _fmt(log.created_at),
        "created_by": "system",
        "updated_by": "system",
    }


def _project(data: dict, fields_param: str | None):
    if not fields_param or fields_param == "all":
        return data
    fields = {f.strip() for f in fields_param.split(",") if f.strip()}
    return {k: v for k, v in data.items() if k in fields}


class ActivityLogPayloadSerializer(serializers.Serializer):
    id = serializers.CharField()
    organization_id = serializers.CharField()
    actor_user_id = serializers.CharField()
    event_type = serializers.CharField()
    target_type = serializers.CharField()
    target_id = serializers.CharField()
    metadata_json = serializers.JSONField()
    request_id = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    created_by = serializers.CharField()
    updated_by = serializers.CharField()


ActivityLogListResponseSerializer = paginated_response_serializer("ActivityLogListResponse", ActivityLogPayloadSerializer)
ACTOR_USER_PARAMETER = OpenApiParameter(
    name="actor_user_id",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Filter by actor user UUID.",
)
EVENT_TYPE_PARAMETER = OpenApiParameter(
    name="event_type",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Filter by event type.",
)
TARGET_TYPE_PARAMETER = OpenApiParameter(
    name="target_type",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Filter by target type.",
)


@extend_schema_view(
    get=extend_schema(
        operation_id="activity_logs_list",
        summary="List organization activity logs",
        parameters=[ORG_HEADER_PARAMETER, SEARCH_PARAMETER, ACTOR_USER_PARAMETER, EVENT_TYPE_PARAMETER, TARGET_TYPE_PARAMETER, sort_parameter("created_at", "event_type", "target_type"), ORDER_PARAMETER, PAGE_PARAMETER, LIMIT_PARAMETER, FIELDS_PARAMETER],
        responses={200: ActivityLogListResponseSerializer},
    )
)
class ActivityLogsListApi(APIView):
    permission_classes = [HasOrganizationContext]
    ALLOWED_SORT = {"created_at", "event_type", "target_type"}

    def get(self, request):
        org = TaskService.get_org_or_404(request.headers.get("X-Organization-ID"))
        role = TaskService.require_role(request.user, org, {"organization_admin", "project_manager"})
        if role not in {"super_admin", "organization_admin", "project_manager"}:
            raise OrgAccessDeniedException(
                "You do not have permission to read activity logs for this organization.",
                extra_details={"required_scope": "activity_logs:read"},
            )

        qs = ActivityLog.objects.filter(organization=org)

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(event_type__icontains=search) | qs.filter(target_type__icontains=search)

        actor_user_id = request.query_params.get("actor_user_id")
        if actor_user_id:
            qs = qs.filter(actor_user_id=actor_user_id)

        event_type = request.query_params.get("event_type")
        if event_type:
            qs = qs.filter(event_type=event_type)

        target_type = request.query_params.get("target_type")
        if target_type:
            qs = qs.filter(target_type=target_type)

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
        items = [_project(_payload(log), fields_param) for log in page_obj.object_list]
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
                "message": "Activity logs retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )
