from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
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
from apps.core.exceptions import ResourceConflictException, TaskStatusInvalidException, TaskUpdateForbiddenException
from apps.core.permissions import HasOrganizationContext
from apps.tasks.models import Task
from apps.tasks.serializers import TaskCreateSerializer, TaskUpdateSerializer
from apps.tasks.services import TaskService


def _fmt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def _payload(task: Task):
    assignee_name = None
    if task.assignee_user_id and getattr(task, "assignee_user", None):
        assignee_name = f"{task.assignee_user.first_name} {task.assignee_user.last_name}".strip() or task.assignee_user.email

    creator_name = None
    if task.created_by_user_id and getattr(task, "created_by_user", None):
        creator_name = f"{task.created_by_user.first_name} {task.created_by_user.last_name}".strip() or task.created_by_user.email

    return {
        "id": str(task.id),
        "project_id": str(task.project_id),
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "due_at": _fmt(task.due_at),
        "assignee_user_id": str(task.assignee_user_id) if task.assignee_user_id else None,
        "assignee_user_name": assignee_name,
        "created_by_user_id": str(task.created_by_user_id),
        "created_by_user_name": creator_name,
        "created_at": _fmt(task.created_at),
        "updated_at": _fmt(task.updated_at),
        "completed_at": _fmt(task.completed_at),
        "created_by": str(task.created_by_user_id),
        "updated_by": str(task.updated_by_user_id) if task.updated_by_user_id else str(task.created_by_user_id),
    }


def _apply_projection(data: dict, fields_param: str | None):
    if not fields_param or fields_param == "all":
        return data
    requested = {f.strip() for f in fields_param.split(",") if f.strip()}
    return {k: v for k, v in data.items() if k in requested}


class TaskPayloadSerializer(serializers.Serializer):
    id = serializers.CharField()
    project_id = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_null=True, allow_blank=True)
    priority = serializers.CharField()
    status = serializers.CharField()
    due_at = serializers.DateTimeField(allow_null=True)
    assignee_user_id = serializers.CharField(allow_null=True)
    assignee_user_name = serializers.CharField(allow_null=True, required=False)
    created_by_user_id = serializers.CharField()
    created_by_user_name = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(allow_null=True)
    created_by = serializers.CharField()
    updated_by = serializers.CharField()
    deleted_at = serializers.DateTimeField(allow_null=True, required=False)


TaskListResponseSerializer = paginated_response_serializer("TaskListResponse", TaskPayloadSerializer)
TaskResponseSerializer = success_response_serializer("TaskResponse", TaskPayloadSerializer)

TASK_ID_PARAMETER = uuid_path_parameter("id", "Task UUID.")
PROJECT_FILTER_PARAMETER = OpenApiParameter(
    name="project_id",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Filter tasks by project UUID.",
)
TASK_STATUS_PARAMETER = OpenApiParameter(
    name="status",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    enum=[Task.STATUS_TODO, Task.STATUS_IN_PROGRESS, Task.STATUS_DONE],
    description="Filter by task status.",
)
TASK_PRIORITY_PARAMETER = OpenApiParameter(
    name="priority",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    enum=[Task.PRIORITY_LOW, Task.PRIORITY_MEDIUM, Task.PRIORITY_HIGH],
    description="Filter by task priority.",
)
ASSIGNEE_PARAMETER = OpenApiParameter(
    name="assignee_user_id",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Filter by assignee user UUID.",
)


@extend_schema_view(
    get=extend_schema(
        operation_id="tasks_list",
        summary="List tasks",
        parameters=[ORG_HEADER_PARAMETER, SEARCH_PARAMETER, PROJECT_FILTER_PARAMETER, TASK_STATUS_PARAMETER, TASK_PRIORITY_PARAMETER, ASSIGNEE_PARAMETER, sort_parameter("title", "priority", "status", "due_at", "created_at"), ORDER_PARAMETER, PAGE_PARAMETER, LIMIT_PARAMETER, FIELDS_PARAMETER],
        responses={200: TaskListResponseSerializer},
    ),
    post=extend_schema(
        operation_id="tasks_create",
        summary="Create a task",
        parameters=[ORG_HEADER_PARAMETER],
        request=TaskCreateSerializer,
        responses={201: TaskResponseSerializer},
    ),
)
class TaskListApi(APIView):
    permission_classes = [HasOrganizationContext]
    ALLOWED_SORT = {"title", "priority", "status", "due_at", "created_at"}
    serializer_class = TaskCreateSerializer

    def get(self, request):
        org = TaskService.get_org_or_404(request.headers.get("X-Organization-ID"))
        TaskService.require_role(request.user, org, TaskService.READ_ROLES)

        qs = Task.objects.select_related("project").filter(project__organization=org, deleted_at__isnull=True)

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(title__icontains=search)

        project_id = request.query_params.get("project_id")
        if project_id:
            project = TaskService.get_project_in_org_or_404(project_id, org)
            qs = qs.filter(project=project)

        status_filter = request.query_params.get("status")
        if status_filter:
            allowed = {Task.STATUS_TODO, Task.STATUS_IN_PROGRESS, Task.STATUS_DONE}
            if status_filter not in allowed:
                raise TaskStatusInvalidException(
                    "Task status must be one of: todo, in_progress, done.",
                    extra_details={"status": status_filter},
                )
            qs = qs.filter(status=status_filter)

        priority_filter = request.query_params.get("priority")
        if priority_filter:
            if priority_filter not in {Task.PRIORITY_LOW, Task.PRIORITY_MEDIUM, Task.PRIORITY_HIGH}:
                from rest_framework.exceptions import ValidationError

                raise ValidationError({"priority": ["Must be one of: low, medium, high."]})
            qs = qs.filter(priority=priority_filter)

        assignee_user_id = request.query_params.get("assignee_user_id")
        if assignee_user_id:
            qs = qs.filter(assignee_user_id=assignee_user_id)

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
        items = [_apply_projection(_payload(task), fields_param) for task in page_obj.object_list]
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
                "message": "Tasks retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        org = TaskService.get_org_or_404(request.headers.get("X-Organization-ID"))
        TaskService.require_role(request.user, org, TaskService.WRITE_ROLES)

        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project_ref = request.data.get("project_id") or serializer.validated_data.get("project_id") or serializer.validated_data.get("project")
        if hasattr(project_ref, "id"):
            project_ref = project_ref.id
        project = TaskService.get_project_in_org_or_404(str(project_ref), org)

        assignee_id = request.data.get("assignee_user_id") or serializer.validated_data.get("assignee_user_id") or serializer.validated_data.get("assignee_user")
        if hasattr(assignee_id, "id"):
            assignee_id = assignee_id.id
        if assignee_id:
            TaskService.validate_assignee_membership(project, str(assignee_id))

        task = serializer.save(
            project=project,
            created_by_user=request.user,
            updated_by_user=request.user,
        )
        if task.status == Task.STATUS_DONE and not task.completed_at:
            task.completed_at = timezone.now()
            task.save(update_fields=["completed_at", "updated_at"])

        return Response(
            {"success": True, "data": _payload(task), "message": "Task created successfully."},
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    post=extend_schema(exclude=True)
)
class TaskCreateApi(APIView):
    permission_classes = [HasOrganizationContext]

    def post(self, request):
        return TaskListApi().post(request)


@extend_schema_view(
    get=extend_schema(
        operation_id="tasks_retrieve",
        summary="Get task details",
        parameters=[ORG_HEADER_PARAMETER, TASK_ID_PARAMETER, FIELDS_PARAMETER],
        responses={200: TaskResponseSerializer},
    ),
    patch=extend_schema(
        operation_id="tasks_update_partial",
        summary="Update a task",
        parameters=[ORG_HEADER_PARAMETER, TASK_ID_PARAMETER],
        request=TaskUpdateSerializer,
        responses={200: TaskResponseSerializer},
    ),
    delete=extend_schema(
        operation_id="tasks_delete",
        summary="Soft-delete a task",
        parameters=[ORG_HEADER_PARAMETER, TASK_ID_PARAMETER],
        responses={200: TaskResponseSerializer},
    ),
)
class TaskDetailApi(APIView):
    permission_classes = [HasOrganizationContext]
    serializer_class = TaskUpdateSerializer

    def _get_task_and_role(self, request, id):
        org = TaskService.get_org_or_404(request.headers.get("X-Organization-ID"))
        role = TaskService.require_role(request.user, org, TaskService.READ_ROLES)
        task = TaskService.get_task_in_org_or_404(id, org)
        return task, role

    def get(self, request, id):
        task, _role = self._get_task_and_role(request, id)
        return Response(
            {
                "success": True,
                "data": _apply_projection(_payload(task), request.query_params.get("fields")),
                "message": "Task retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, id):
        task, role = self._get_task_and_role(request, id)
        if role not in TaskService.WRITE_ROLES and role != "super_admin":
            raise TaskUpdateForbiddenException(
                "Insufficient permissions to update task.",
                extra_details={"task_id": str(task.id)},
            )
        if role == "team_member" and task.assignee_user_id != request.user.id:
            raise TaskUpdateForbiddenException(
                "Team members may only update tasks assigned to themselves.",
                extra_details={"task_id": str(task.id), "assignee_user_id": str(task.assignee_user_id) if task.assignee_user_id else None},
            )

        serializer = TaskUpdateSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        assignee_id = request.data.get("assignee_user_id") or serializer.validated_data.get("assignee_user_id") or serializer.validated_data.get("assignee_user")
        if hasattr(assignee_id, "id"):
            assignee_id = assignee_id.id
        if assignee_id:
            TaskService.validate_assignee_membership(task.project, str(assignee_id))

        due_at = serializer.validated_data.get("due_at")
        if due_at and due_at < task.created_at:
            from apps.core.exceptions import ProjectDeadlineInvalidException

            raise ProjectDeadlineInvalidException(
                "due_at must be greater than task creation time.",
                extra_details={"due_at": _fmt(due_at)},
            )

        updated = serializer.save(updated_by_user=request.user)
        if "status" in serializer.validated_data:
            if updated.status == Task.STATUS_DONE:
                updated.completed_at = timezone.now()
            else:
                updated.completed_at = None
            updated.save(update_fields=["completed_at", "updated_at"])

        return Response(
            {"success": True, "data": _payload(updated), "message": "Task updated successfully."},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, id):
        task, role = self._get_task_and_role(request, id)
        if role not in TaskService.ADMIN_ROLES and role != "super_admin":
            raise TaskUpdateForbiddenException(
                "Insufficient permissions to delete task.",
                extra_details={"task_id": str(task.id)},
            )
        if task.deleted_at:
            raise ResourceConflictException(
                "This task has already been deleted.",
                extra_details={"task_id": str(task.id), "current_state": "deleted"},
            )
        task.deleted_at = timezone.now()
        task.updated_by_user = request.user
        task.save(update_fields=["deleted_at", "updated_by_user", "updated_at"])
        payload = _payload(task)
        payload["deleted_at"] = _fmt(task.deleted_at)
        return Response(
            {"success": True, "data": payload, "message": "Task soft-deleted successfully."},
            status=status.HTTP_200_OK,
        )
