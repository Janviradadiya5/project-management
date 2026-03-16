from uuid import UUID

from drf_spectacular.utils import extend_schema, extend_schema_view
from django.core.paginator import EmptyPage, Paginator
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comments.models import Comment
from apps.comments.serializers import CommentCreateSerializer, CommentUpdateSerializer
from apps.comments.services import CommentService
from apps.core.openapi import FIELDS_PARAMETER, LIMIT_PARAMETER, ORDER_PARAMETER, ORG_HEADER_PARAMETER, PAGE_PARAMETER, SEARCH_PARAMETER, paginated_response_serializer, success_response_serializer, uuid_path_parameter
from apps.core.exceptions import (
    CommentParentMismatchException,
    OrgAccessDeniedException,
    ResourceConflictException,
    ResourceNotFoundException,
    TaskUpdateForbiddenException,
)
from apps.core.permissions import HasOrganizationContext
from apps.tasks.services import TaskService


def _fmt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def _display_name(user):
    if not user:
        return None
    full_name = f"{user.first_name} {user.last_name}".strip()
    return full_name or user.email


def _comment_payload(comment: Comment, updated_by_id=None):
    actor_id = updated_by_id or comment.author_user_id
    return {
        "id": str(comment.id),
        "task_id": str(comment.task_id),
        "author_user_id": str(comment.author_user_id),
        "author_user_name": _display_name(getattr(comment, "author_user", None)),
        "author_user_email": getattr(getattr(comment, "author_user", None), "email", None),
        "parent_comment_id": str(comment.parent_comment_id) if comment.parent_comment_id else None,
        "body": comment.body,
        "is_edited": comment.is_edited,
        "deleted_at": _fmt(comment.deleted_at),
        "created_at": _fmt(comment.created_at),
        "updated_at": _fmt(comment.updated_at),
        "created_by": str(comment.author_user_id),
        "updated_by": str(actor_id),
    }


class CommentPayloadSerializer(serializers.Serializer):
    id = serializers.CharField()
    task_id = serializers.CharField()
    author_user_id = serializers.CharField()
    author_user_name = serializers.CharField(allow_null=True, required=False)
    author_user_email = serializers.EmailField(allow_null=True, required=False)
    parent_comment_id = serializers.CharField(allow_null=True)
    body = serializers.CharField()
    is_edited = serializers.BooleanField()
    deleted_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    created_by = serializers.CharField()
    updated_by = serializers.CharField()


CommentResponseSerializer = success_response_serializer("CommentResponse", CommentPayloadSerializer)
CommentListResponseSerializer = paginated_response_serializer("CommentListResponse", CommentPayloadSerializer)
TASK_ID_PARAMETER = uuid_path_parameter("task_id", "Task UUID.")
COMMENT_ID_PARAMETER = uuid_path_parameter("id", "Comment UUID.")


@extend_schema_view(
    get=extend_schema(
        operation_id="tasks_comments_list",
        summary="List task comments",
        parameters=[ORG_HEADER_PARAMETER, TASK_ID_PARAMETER, SEARCH_PARAMETER, PAGE_PARAMETER, LIMIT_PARAMETER, ORDER_PARAMETER, FIELDS_PARAMETER],
        responses={200: CommentListResponseSerializer},
    ),
    post=extend_schema(
        operation_id="tasks_comments_create",
        summary="Create a task comment",
        parameters=[ORG_HEADER_PARAMETER, TASK_ID_PARAMETER],
        request=CommentCreateSerializer,
        responses={201: CommentResponseSerializer},
    )
)
class TaskCommentsListApi(APIView):
    permission_classes = [HasOrganizationContext]
    serializer_class = CommentCreateSerializer

    def get(self, request, task_id):
        org = TaskService.get_org_or_404(request.headers.get("X-Organization-ID"))
        task = TaskService.get_task_in_org_or_404(task_id, org)

        if not CommentService.can_write_comment(request.user, task) and not CommentService.is_active_project_member(request.user, task) and not CommentService.is_super_admin(request.user):
            raise OrgAccessDeniedException(
                "You do not have permission to view comments for this task.",
                extra_details={"task_id": str(task.id)},
            )

        comments_qs = Comment.objects.select_related("author_user").filter(task=task, deleted_at__isnull=True)
        search = request.query_params.get("search")
        if search:
            comments_qs = comments_qs.filter(body__icontains=search)

        order = request.query_params.get("order", "desc")
        if order not in {"asc", "desc"}:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"order": ["Order must be asc or desc."]})
        comments_qs = comments_qs.order_by("created_at" if order == "asc" else "-created_at")

        try:
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 50))
        except (TypeError, ValueError) as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"page": ["Must be an integer."], "limit": ["Must be an integer."]}) from exc
        if page < 1 or not (1 <= limit <= 100):
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"limit": ["Limit must be between 1 and 100."]})

        paginator = Paginator(comments_qs, limit)
        try:
            page_obj = paginator.page(page)
        except EmptyPage as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"page": ["Requested page is out of range."]}) from exc

        fields_param = request.query_params.get("fields")
        items = []
        for comment in page_obj.object_list:
            payload = _comment_payload(comment)
            if fields_param and fields_param != "all":
                requested = {field.strip() for field in fields_param.split(",") if field.strip()}
                payload = {key: value for key, value in payload.items() if key in requested}
            items.append(payload)

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
                "message": "Comments retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, task_id):
        org = TaskService.get_org_or_404(request.headers.get("X-Organization-ID"))
        task = TaskService.get_task_in_org_or_404(task_id, org)

        if not CommentService.can_write_comment(request.user, task):
            raise OrgAccessDeniedException(
                "You do not have permission to comment.",
                extra_details={"task_id": str(task.id)},
            )

        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parent_comment_id = serializer.validated_data.get("parent_comment_id")
        parent_comment = None
        if parent_comment_id:
            try:
                parent_comment = Comment.objects.get(id=parent_comment_id)
            except Comment.DoesNotExist as exc:
                raise ResourceNotFoundException(
                    "Parent comment not found.",
                    extra_details={"parent_comment_id": str(parent_comment_id)},
                ) from exc
            if parent_comment.task_id != task.id:
                raise CommentParentMismatchException(
                    "The parent comment must belong to the same task.",
                    extra_details={"task_id": str(task.id), "parent_comment_id": str(parent_comment_id)},
                )

        comment = serializer.save(task=task, author_user=request.user, parent_comment=parent_comment)
        return Response(
            {"success": True, "data": _comment_payload(comment), "message": "Comment created successfully."},
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    patch=extend_schema(
        operation_id="comments_update",
        summary="Update a comment",
        parameters=[ORG_HEADER_PARAMETER, COMMENT_ID_PARAMETER],
        request=CommentUpdateSerializer,
        responses={200: CommentResponseSerializer},
    ),
    delete=extend_schema(
        operation_id="comments_delete",
        summary="Soft-delete a comment",
        parameters=[ORG_HEADER_PARAMETER, COMMENT_ID_PARAMETER],
        responses={200: CommentResponseSerializer},
    ),
)
class CommentUpdateApi(APIView):
    permission_classes = [HasOrganizationContext]
    serializer_class = CommentUpdateSerializer

    def _get_comment(self, request, id):
        try:
            UUID(str(id))
        except ValueError as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"id": ["Must be a valid UUID."]}) from exc

        org = TaskService.get_org_or_404(request.headers.get("X-Organization-ID"))
        try:
            comment = Comment.objects.select_related("task", "task__project").get(id=id)
        except Comment.DoesNotExist as exc:
            raise ResourceNotFoundException("Comment not found.", extra_details={"comment_id": str(id)}) from exc

        if comment.task.project.organization_id != org.id:
            raise OrgAccessDeniedException(
                "You do not have permission to access this comment.",
                extra_details={"comment_id": str(id)},
            )
        if comment.deleted_at:
            raise ResourceNotFoundException("Comment not found or deleted.", extra_details={"comment_id": str(id)})
        return comment

    def patch(self, request, id):
        comment = self._get_comment(request, id)
        if not CommentService.can_edit_or_delete_comment(request.user, comment):
            raise TaskUpdateForbiddenException(
                "You are not allowed to edit this comment.",
                extra_details={"comment_id": str(comment.id), "actor_user_id": str(request.user.id)},
            )
        serializer = CommentUpdateSerializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save(is_edited=True)
        return Response(
            {"success": True, "data": _comment_payload(updated, updated_by_id=request.user.id), "message": "Comment updated successfully."},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, id):
        comment = self._get_comment(request, id)
        if not CommentService.can_edit_or_delete_comment(request.user, comment):
            raise TaskUpdateForbiddenException(
                "You do not have permission to delete comment.",
                extra_details={"comment_id": str(comment.id), "actor_user_id": str(request.user.id)},
            )
        if comment.deleted_at:
            raise ResourceConflictException(
                "This comment has already been deleted.",
                extra_details={"comment_id": str(comment.id), "current_state": "deleted"},
            )
        comment.deleted_at = timezone.now()
        comment.save(update_fields=["deleted_at", "updated_at"])
        return Response(
            {"success": True, "data": _comment_payload(comment, updated_by_id=request.user.id), "message": "Comment soft-deleted successfully."},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    delete=extend_schema(exclude=True)
)
class CommentDeleteApi(APIView):
    permission_classes = [HasOrganizationContext]

    def delete(self, request, id):
        return CommentUpdateApi().delete(request, id)
