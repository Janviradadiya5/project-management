from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from django.core.paginator import EmptyPage, Paginator
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ProjectDeadlineInvalidException, ResourceConflictException, ResourceNotFoundException
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
from apps.core.permissions import HasOrganizationContext
from apps.projects.models import Project, ProjectMember
from apps.projects.serializers import ProjectCreateSerializer, ProjectMemberAddSerializer, ProjectUpdateSerializer
from apps.projects.services import ProjectService


def _fmt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def _display_name(user):
    if not user:
        return None
    full_name = f"{user.first_name} {user.last_name}".strip()
    return full_name or user.email


def _project_payload(project: Project):
    return {
        "id": str(project.id),
        "organization_id": str(project.organization_id),
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "deadline_at": _fmt(project.deadline_at),
        "created_by_user_id": str(project.created_by_user_id),
        "created_by_user_name": _display_name(getattr(project, "created_by_user", None)),
        "created_at": _fmt(project.created_at),
        "updated_at": _fmt(project.updated_at),
        "created_by": str(project.created_by_user_id),
        "updated_by": str(project.updated_by_user_id) if project.updated_by_user_id else str(project.created_by_user_id),
    }


def _member_payload(member):
    return {
        "id": str(member.id),
        "project_id": str(member.project_id),
        "user_id": str(member.user_id),
        "user_name": _display_name(getattr(member, "user", None)),
        "user_email": getattr(getattr(member, "user", None), "email", None),
        "project_role": member.project_role,
        "added_by_user_id": str(member.added_by_user_id),
        "added_by_user_name": _display_name(getattr(member, "added_by_user", None)),
        "created_at": _fmt(member.created_at),
        "updated_at": _fmt(member.created_at),
        "created_by": str(member.added_by_user_id),
        "updated_by": str(member.added_by_user_id),
    }


def _apply_projection(data: dict, fields_param: str | None):
    if not fields_param or fields_param == "all":
        return data
    requested = {f.strip() for f in fields_param.split(",") if f.strip()}
    return {k: v for k, v in data.items() if k in requested}


class ProjectPayloadSerializer(serializers.Serializer):
    id = serializers.CharField()
    organization_id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True, allow_blank=True)
    status = serializers.CharField()
    deadline_at = serializers.DateTimeField(allow_null=True)
    created_by_user_id = serializers.CharField()
    created_by_user_name = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    created_by = serializers.CharField()
    updated_by = serializers.CharField()


class ProjectMemberPayloadSerializer(serializers.Serializer):
    id = serializers.CharField()
    project_id = serializers.CharField()
    user_id = serializers.CharField()
    user_name = serializers.CharField(allow_null=True, required=False)
    user_email = serializers.EmailField(allow_null=True, required=False)
    project_role = serializers.CharField()
    added_by_user_id = serializers.CharField()
    added_by_user_name = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    created_by = serializers.CharField()
    updated_by = serializers.CharField()
    removed_at = serializers.DateTimeField(allow_null=True, required=False)


ProjectListResponseSerializer = paginated_response_serializer("ProjectListResponse", ProjectPayloadSerializer)
ProjectResponseSerializer = success_response_serializer("ProjectResponse", ProjectPayloadSerializer)
ProjectMembersListResponseSerializer = paginated_response_serializer("ProjectMembersListResponse", ProjectMemberPayloadSerializer)
ProjectMemberResponseSerializer = success_response_serializer("ProjectMemberResponse", ProjectMemberPayloadSerializer)

PROJECT_ID_PARAMETER = uuid_path_parameter("id", "Project UUID.")
PROJECT_MEMBER_ID_PARAMETER = uuid_path_parameter("project_member_id", "Project member UUID.")
PROJECT_STATUS_PARAMETER = OpenApiParameter(
    name="status",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    enum=[Project.STATUS_ACTIVE, Project.STATUS_COMPLETED, Project.STATUS_ARCHIVED],
    description="Filter by project status.",
)
PROJECT_ORG_FILTER_PARAMETER = OpenApiParameter(
    name="organization_id",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Optional organization filter. Must match X-Organization-ID when provided.",
)


@extend_schema_view(
    get=extend_schema(
        operation_id="projects_list",
        summary="List projects",
        parameters=[ORG_HEADER_PARAMETER, PROJECT_ORG_FILTER_PARAMETER, SEARCH_PARAMETER, PROJECT_STATUS_PARAMETER, sort_parameter("name", "status", "deadline_at", "created_at", "updated_at"), ORDER_PARAMETER, PAGE_PARAMETER, LIMIT_PARAMETER, FIELDS_PARAMETER],
        responses={200: ProjectListResponseSerializer},
    ),
    post=extend_schema(
        operation_id="projects_create",
        summary="Create a project",
        parameters=[ORG_HEADER_PARAMETER],
        request=ProjectCreateSerializer,
        responses={201: ProjectResponseSerializer},
    ),
)
class ProjectListApi(APIView):
    permission_classes = [HasOrganizationContext]
    ALLOWED_SORT = {"name", "status", "deadline_at", "created_at", "updated_at"}
    serializer_class = ProjectCreateSerializer

    def get(self, request):
        org = ProjectService.get_org_or_404(request.headers.get("X-Organization-ID"))
        ProjectService.require_org_role(request.user, org, ProjectService.READ_ROLES)

        org_filter = request.query_params.get("organization_id")
        if org_filter and str(org_filter) != str(org.id):
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"organization_id": ["Must match X-Organization-ID."]})

        queryset = Project.objects.filter(organization=org, deleted_at__isnull=True)

        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        status_filter = request.query_params.get("status")
        if status_filter:
            allowed_status = {Project.STATUS_ACTIVE, Project.STATUS_COMPLETED, Project.STATUS_ARCHIVED}
            if status_filter not in allowed_status:
                from apps.core.exceptions import ProjectStatusInvalidException

                raise ProjectStatusInvalidException(
                    "Status filter value is invalid.",
                    extra_details={"status": status_filter},
                )
            queryset = queryset.filter(status=status_filter)

        sort_by = request.query_params.get("sort_by", "created_at")
        if sort_by not in self.ALLOWED_SORT:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"sort_by": ["Invalid sort field."]})
        order = request.query_params.get("order", "desc")
        if order not in {"asc", "desc"}:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"order": ["Order must be asc or desc."]})
        queryset = queryset.order_by(sort_by if order == "asc" else f"-{sort_by}")

        try:
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 20))
        except (TypeError, ValueError) as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"page": ["Must be an integer."], "limit": ["Must be an integer."]}) from exc
        if page < 1 or not (1 <= limit <= 100):
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"limit": ["Limit must be between 1 and 100."]})

        paginator = Paginator(queryset, limit)
        try:
            page_obj = paginator.page(page)
        except EmptyPage as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"page": ["Requested page is out of range."]}) from exc

        fields_param = request.query_params.get("fields")
        items = [_apply_projection(_project_payload(project), fields_param) for project in page_obj.object_list]
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
                "message": "Projects retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        org = ProjectService.get_org_or_404(request.headers.get("X-Organization-ID"))
        ProjectService.require_org_role(request.user, org, ProjectService.WRITE_ROLES)

        serializer = ProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if Project.objects.filter(organization=org, name=serializer.validated_data["name"], deleted_at__isnull=True).exists():
            raise ResourceConflictException(
                "Project name already exists in this organization.",
                extra_details={"name": serializer.validated_data["name"], "organization_id": str(org.id)},
            )

        project = serializer.save(
            organization=org,
            created_by_user=request.user,
            updated_by_user=request.user,
        )
        ProjectMember.objects.get_or_create(
            project=project,
            user=request.user,
            defaults={
                "project_role": ProjectMember.ROLE_MANAGER,
                "added_by_user": request.user,
                "created_by": request.user,
                "updated_by": request.user,
            },
        )
        return Response(
            {
                "success": True,
                "data": _project_payload(project),
                "message": "Project created successfully.",
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    post=extend_schema(exclude=True)
)
class ProjectCreateApi(APIView):
    permission_classes = [HasOrganizationContext]

    def post(self, request):
        return ProjectListApi().post(request)


@extend_schema_view(
    get=extend_schema(
        operation_id="projects_retrieve",
        summary="Get project details",
        parameters=[ORG_HEADER_PARAMETER, PROJECT_ID_PARAMETER, FIELDS_PARAMETER],
        responses={200: ProjectResponseSerializer},
    ),
    patch=extend_schema(
        operation_id="projects_update_partial",
        summary="Update a project",
        parameters=[ORG_HEADER_PARAMETER, PROJECT_ID_PARAMETER],
        request=ProjectUpdateSerializer,
        responses={200: ProjectResponseSerializer},
    ),
    delete=extend_schema(
        operation_id="projects_archive",
        summary="Archive a project",
        parameters=[ORG_HEADER_PARAMETER, PROJECT_ID_PARAMETER],
        responses={200: ProjectResponseSerializer},
    ),
)
class ProjectDetailApi(APIView):
    permission_classes = [HasOrganizationContext]
    serializer_class = ProjectUpdateSerializer

    def _resolve(self, request, id):
        org = ProjectService.get_org_or_404(request.headers.get("X-Organization-ID"))
        project = ProjectService.get_project_or_404(id, org)
        return org, project

    def get(self, request, id):
        org, project = self._resolve(request, id)
        ProjectService.require_org_role(request.user, org, ProjectService.READ_ROLES)
        return Response(
            {
                "success": True,
                "data": _apply_projection(_project_payload(project), request.query_params.get("fields")),
                "message": "Project retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, id):
        org, project = self._resolve(request, id)
        ProjectService.require_org_role(request.user, org, ProjectService.WRITE_ROLES)

        if project.status == Project.STATUS_ARCHIVED:
            raise ResourceConflictException(
                "Project is archived and cannot be modified with this operation.",
                extra_details={"project_id": str(project.id), "status": project.status},
            )

        serializer = ProjectUpdateSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_name = serializer.validated_data.get("name")
        if new_name and Project.objects.filter(organization=org, name=new_name, deleted_at__isnull=True).exclude(id=project.id).exists():
            raise ResourceConflictException(
                "Project name conflict within organization.",
                extra_details={"name": new_name, "organization_id": str(org.id)},
            )

        deadline_at = serializer.validated_data.get("deadline_at")
        if deadline_at and deadline_at < project.created_at:
            raise ProjectDeadlineInvalidException(
                "deadline_at must be greater than created_at.",
                extra_details={"deadline_at": _fmt(deadline_at)},
            )

        project = serializer.save(updated_by_user=request.user)
        return Response(
            {
                "success": True,
                "data": _project_payload(project),
                "message": "Project updated successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, id):
        org, project = self._resolve(request, id)
        ProjectService.require_org_role(request.user, org, ProjectService.ADMIN_ROLES)

        if project.status == Project.STATUS_ARCHIVED:
            raise ResourceConflictException(
                "The project is already archived and cannot be archived again.",
                extra_details={"project_id": str(project.id), "current_status": project.status},
            )

        project.status = Project.STATUS_ARCHIVED
        project.updated_by_user = request.user
        project.save(update_fields=["status", "updated_by_user", "updated_at"])
        return Response(
            {
                "success": True,
                "data": _project_payload(project),
                "message": "Project archived successfully.",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="projects_members_list",
        summary="List project members",
        parameters=[ORG_HEADER_PARAMETER, PROJECT_ID_PARAMETER, PAGE_PARAMETER, LIMIT_PARAMETER, FIELDS_PARAMETER],
        responses={200: ProjectMembersListResponseSerializer},
    ),
    post=extend_schema(
        operation_id="projects_members_add",
        summary="Add a member to project",
        parameters=[ORG_HEADER_PARAMETER, PROJECT_ID_PARAMETER],
        request=ProjectMemberAddSerializer,
        responses={201: ProjectMemberResponseSerializer},
    )
)
class ProjectAddMemberApi(APIView):
    permission_classes = [HasOrganizationContext]
    serializer_class = ProjectMemberAddSerializer

    def get(self, request, id):
        org = ProjectService.get_org_or_404(request.headers.get("X-Organization-ID"))
        ProjectService.require_org_role(request.user, org, ProjectService.READ_ROLES)
        project = ProjectService.get_project_or_404(id, org)

        try:
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 50))
        except (TypeError, ValueError) as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"page": ["Must be an integer."], "limit": ["Must be an integer."]}) from exc
        if page < 1 or not (1 <= limit <= 100):
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"limit": ["Limit must be between 1 and 100."]})

        members_qs = ProjectMember.objects.select_related("user", "added_by_user").filter(project=project).order_by("user__first_name", "user__last_name", "user__email")
        paginator = Paginator(members_qs, limit)
        try:
            page_obj = paginator.page(page)
        except EmptyPage as exc:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"page": ["Requested page is out of range."]}) from exc

        fields_param = request.query_params.get("fields")
        items = [_apply_projection(_member_payload(member), fields_param) for member in page_obj.object_list]
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
                "message": "Project members retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, id):
        org = ProjectService.get_org_or_404(request.headers.get("X-Organization-ID"))
        ProjectService.require_org_role(request.user, org, ProjectService.WRITE_ROLES)
        project = ProjectService.get_project_or_404(id, org)

        serializer = ProjectMemberAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = ProjectService.add_member_strict(
            project=project,
            user_id=serializer.validated_data["user_id"],
            role_code=serializer.validated_data["project_role"],
            added_by=request.user,
        )
        return Response(
            {
                "success": True,
                "data": _member_payload(member),
                "message": "Project member added successfully.",
            },
            status=status.HTTP_201_CREATED,
        )


class ProjectRemoveMemberApi(APIView):
    permission_classes = [HasOrganizationContext]

    @extend_schema(
        operation_id="projects_members_remove",
        summary="Remove a member from project",
        parameters=[ORG_HEADER_PARAMETER, PROJECT_ID_PARAMETER, PROJECT_MEMBER_ID_PARAMETER],
        responses={200: ProjectMemberResponseSerializer},
    )
    def delete(self, request, id, project_member_id):
        org = ProjectService.get_org_or_404(request.headers.get("X-Organization-ID"))
        ProjectService.require_org_role(request.user, org, ProjectService.WRITE_ROLES)
        project = ProjectService.get_project_or_404(id, org)

        try:
            member = ProjectMember.objects.get(id=project_member_id, project=project)
        except ProjectMember.DoesNotExist as exc:
            raise ResourceNotFoundException(
                "Project member not found.",
                extra_details={"project_id": str(project.id), "project_member_id": str(project_member_id)},
            ) from exc

        data = _member_payload(member)
        data["removed_at"] = _fmt(member.updated_at)
        member.delete()
        return Response(
            {
                "success": True,
                "data": data,
                "message": "Project member removed successfully.",
            },
            status=status.HTTP_200_OK,
        )
