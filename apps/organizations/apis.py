from uuid import UUID

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.openapi import (
    FIELDS_PARAMETER,
    LIMIT_PARAMETER,
    ORDER_PARAMETER,
    PAGE_PARAMETER,
    SEARCH_PARAMETER,
    paginated_response_serializer,
    sort_parameter,
    success_response_serializer,
    uuid_path_parameter,
)
from apps.core.exceptions import OrgAccessDeniedException, OrgNotFoundOrDeletedException, ResourceConflictException
from apps.core.permissions import IsAuthenticatedAndVerified
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMembership
from apps.organizations.serializers import (
    AcceptInviteSerializer,
    InviteMemberSerializer,
    OrganizationCreateSerializer,
    OrganizationUpdateSerializer,
    UpdateMembershipSerializer,
)
from apps.organizations.services import OrganizationService


def _fmt(dt) -> str | None:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def _display_name(user) -> str | None:
    if not user:
        return None
    full_name = f"{user.first_name} {user.last_name}".strip()
    return full_name or user.email


def _membership_payload(membership: OrganizationMembership, updated_by_id=None) -> dict:
    fallback_by = str(membership.invited_by_user_id) if membership.invited_by_user_id else None
    return {
        "id": str(membership.id),
        "organization_id": str(membership.organization_id),
        "user_id": str(membership.user_id),
        "user_name": _display_name(getattr(membership, "user", None)),
        "user_email": getattr(getattr(membership, "user", None), "email", None),
        "role_id": str(membership.role_id),
        "role_code": membership.role.code,
        "role_name": membership.role.name,
        "status": membership.status,
        "joined_at": _fmt(membership.joined_at),
        "invited_by_user_id": fallback_by,
        "invited_by_user_name": _display_name(getattr(membership, "invited_by_user", None)),
        "created_at": _fmt(membership.created_at),
        "updated_at": _fmt(membership.updated_at),
        "created_by": fallback_by,
        "updated_by": str(updated_by_id) if updated_by_id else fallback_by,
    }


def _invite_payload(invite: OrganizationInvite) -> dict:
    inv_by = str(invite.invited_by_user_id)
    return {
        "id": str(invite.id),
        "organization_id": str(invite.organization_id),
        "email": invite.email,
        "role_id": str(invite.role_id),
        "role_code": invite.role.code,
        "role_name": invite.role.name,
        "expires_at": _fmt(invite.expires_at),
        "accepted_at": _fmt(invite.accepted_at),
        "revoked_at": _fmt(invite.revoked_at),
        "invited_by_user_id": inv_by,
        "invited_by_user_name": _display_name(getattr(invite, "invited_by_user", None)),
        "created_at": _fmt(invite.created_at),
        "updated_at": _fmt(invite.created_at),  # model has no updated_at
        "created_by": inv_by,
        "updated_by": inv_by,
    }


def _organization_payload(org: Organization, user=None) -> dict:
    current_user_role_code = None
    current_user_membership_status = None

    if user is not None:
        if getattr(user, "is_superuser", False):
            current_user_role_code = "super_admin"
            current_user_membership_status = "active"
        else:
            membership = (
                OrganizationMembership.objects.select_related("role")
                .filter(organization=org, user=user)
                .first()
            )
            if membership:
                current_user_role_code = membership.role.code
                current_user_membership_status = membership.status

    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "owner_user_id": str(org.owner_user_id),
        "status": org.status,
        "deleted_at": org.deleted_at.strftime("%Y-%m-%dT%H:%M:%SZ") if org.deleted_at else None,
        "created_at": org.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": org.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "created_by": str(org.created_by_id) if org.created_by_id else None,
        "updated_by": str(org.updated_by_id) if org.updated_by_id else None,
        "current_user_role_code": current_user_role_code,
        "current_user_membership_status": current_user_membership_status,
        "current_user_is_owner": bool(user and org.owner_user_id == user.id),
    }


def _apply_field_projection(data: dict, fields_param: str | None) -> dict:
    if not fields_param or fields_param == "all":
        return data
    requested = {field.strip() for field in fields_param.split(",") if field.strip()}
    return {key: value for key, value in data.items() if key in requested}


def _validate_uuid(value: str) -> None:
    try:
        UUID(str(value))
    except ValueError as exc:
        from rest_framework.exceptions import ValidationError

        raise ValidationError({"id": ["Provided ID is not a valid UUID."]}) from exc


class OrganizationPayloadSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    slug = serializers.CharField()
    owner_user_id = serializers.CharField()
    status = serializers.CharField()
    deleted_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    created_by = serializers.CharField(allow_null=True)
    updated_by = serializers.CharField(allow_null=True)
    current_user_role_code = serializers.CharField(allow_null=True, required=False)
    current_user_membership_status = serializers.CharField(allow_null=True, required=False)
    current_user_is_owner = serializers.BooleanField(required=False)


class OrganizationMembershipPayloadSerializer(serializers.Serializer):
    id = serializers.CharField()
    organization_id = serializers.CharField()
    user_id = serializers.CharField()
    user_name = serializers.CharField(allow_null=True, required=False)
    user_email = serializers.EmailField(allow_null=True, required=False)
    role_id = serializers.CharField()
    role_code = serializers.CharField()
    role_name = serializers.CharField(allow_null=True, required=False)
    status = serializers.CharField()
    joined_at = serializers.DateTimeField(allow_null=True)
    invited_by_user_id = serializers.CharField(allow_null=True)
    invited_by_user_name = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    created_by = serializers.CharField(allow_null=True)
    updated_by = serializers.CharField(allow_null=True)
    removed_at = serializers.DateTimeField(allow_null=True, required=False)


class OrganizationInvitePayloadSerializer(serializers.Serializer):
    id = serializers.CharField()
    organization_id = serializers.CharField()
    email = serializers.EmailField()
    role_id = serializers.CharField()
    role_code = serializers.CharField()
    role_name = serializers.CharField(allow_null=True, required=False)
    expires_at = serializers.DateTimeField()
    accepted_at = serializers.DateTimeField(allow_null=True)
    revoked_at = serializers.DateTimeField(allow_null=True)
    invited_by_user_id = serializers.CharField()
    invited_by_user_name = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    created_by = serializers.CharField()
    updated_by = serializers.CharField()


OrganizationListResponseSerializer = paginated_response_serializer(
    "OrganizationListResponse",
    OrganizationPayloadSerializer,
)
OrganizationResponseSerializer = success_response_serializer(
    "OrganizationResponse",
    OrganizationPayloadSerializer,
)
OrganizationMembersListResponseSerializer = paginated_response_serializer(
    "OrganizationMembersListResponse",
    OrganizationMembershipPayloadSerializer,
)
OrganizationMemberResponseSerializer = success_response_serializer(
    "OrganizationMemberResponse",
    OrganizationMembershipPayloadSerializer,
)
OrganizationInvitesListResponseSerializer = paginated_response_serializer(
    "OrganizationInvitesListResponse",
    OrganizationInvitePayloadSerializer,
)
OrganizationInviteResponseSerializer = success_response_serializer(
    "OrganizationInviteResponse",
    OrganizationInvitePayloadSerializer,
)
InviteRevocationResponseSerializer = success_response_serializer(
    "OrganizationInviteRevocationResponse",
    inline_serializer(
        name="OrganizationInviteRevocationData",
        fields={
            "id": serializers.CharField(),
            "organization_id": serializers.CharField(),
            "email": serializers.EmailField(),
            "revoked_at": serializers.DateTimeField(),
            "updated_at": serializers.DateTimeField(),
            "updated_by": serializers.CharField(),
            "created_at": serializers.DateTimeField(),
            "created_by": serializers.CharField(),
        }
    ),
)
AcceptInviteResponseSerializer = success_response_serializer(
    "AcceptInviteResponse",
    inline_serializer(
        name="AcceptInviteData",
        fields={
            "membership": OrganizationMembershipPayloadSerializer(),
            "invite": inline_serializer(
                name="AcceptedInviteDetails",
                fields={
                    "id": serializers.CharField(),
                    "accepted_at": serializers.DateTimeField(),
                }
            ),
        }
    ),
)

ORG_PATH_PARAMETER = uuid_path_parameter("org_id", "Organization UUID.")
ORG_ID_PATH_PARAMETER = uuid_path_parameter("id", "Organization UUID.")
USER_ID_PATH_PARAMETER = uuid_path_parameter("user_id", "User UUID.")
INVITE_ID_PATH_PARAMETER = uuid_path_parameter("invite_id", "Invitation UUID.")
STATUS_PARAMETER = OpenApiParameter(
    name="status",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Filter by resource status.",
)
ROLE_ID_PARAMETER = OpenApiParameter(
    name="role_id",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Filter by role UUID.",
)


@extend_schema_view(
    get=extend_schema(
        operation_id="organizations_list",
        summary="List organizations",
        parameters=[SEARCH_PARAMETER, STATUS_PARAMETER, sort_parameter("name", "slug", "created_at", "status", "updated_at"), ORDER_PARAMETER, PAGE_PARAMETER, LIMIT_PARAMETER, FIELDS_PARAMETER],
        responses={200: OrganizationListResponseSerializer},
    ),
    post=extend_schema(
        operation_id="organizations_create",
        summary="Create an organization",
        request=OrganizationCreateSerializer,
        responses={201: OrganizationResponseSerializer},
    ),
)
class OrganizationListApi(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = OrganizationCreateSerializer

    ALLOWED_SORT_FIELDS = {"name", "slug", "created_at", "status", "updated_at"}
    ALLOWED_FIELDS = {"id", "name", "slug", "status", "owner_user_id", "created_at", "updated_at", "deleted_at", "created_by", "updated_by"}

    def get_queryset(self, request):
        queryset = Organization.objects.all()
        if not OrganizationService.is_super_admin(request.user):
            queryset = queryset.filter(memberships__user=request.user, memberships__status=OrganizationMembership.STATUS_ACTIVE).distinct()

        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(slug__icontains=search))

        status_filter = request.query_params.get("status")
        if status_filter:
            if status_filter == "deleted":
                queryset = queryset.filter(deleted_at__isnull=False)
            else:
                queryset = queryset.filter(status=status_filter, deleted_at__isnull=True)

        sort_by = request.query_params.get("sort_by", "created_at")
        if sort_by not in self.ALLOWED_SORT_FIELDS:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"sort_by": ["Invalid sort field."]})
        order = request.query_params.get("order", "desc")
        if order not in {"asc", "desc"}:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"order": ["Order must be asc or desc."]})
        ordering = sort_by if order == "asc" else f"-{sort_by}"
        return queryset.order_by(ordering)

    def get(self, request):
        queryset = self.get_queryset(request)
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 20))
        if page < 1 or limit < 1 or limit > 100:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"page": ["Page must be >= 1."], "limit": ["Limit must be between 1 and 100."]})

        paginator = Paginator(queryset, limit)
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"page": ["Requested page is out of range."]})

        fields_param = request.query_params.get("fields")
        items = [_apply_field_projection(_organization_payload(org, request.user), fields_param) for org in page_obj.object_list]
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
                "message": "Organizations retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if Organization.objects.filter(slug=serializer.validated_data["slug"]).exists():
            raise ResourceConflictException(
                "An organization with this slug already exists. Please choose a different slug.",
                extra_details={"slug": serializer.validated_data["slug"]},
            )
        admin_role = OrganizationService.get_or_create_admin_role()
        org = serializer.save(
            owner_user=request.user,
            created_by=request.user,
            updated_by=request.user,
        )
        OrganizationMembership.objects.get_or_create(
            organization=org,
            user=request.user,
            defaults={
                "role": admin_role,
                "status": OrganizationMembership.STATUS_ACTIVE,
                "joined_at": timezone.now(),
                "invited_by_user": request.user,
            },
        )
        return Response(
            {
                "success": True,
                "data": _organization_payload(org, request.user),
                "message": "Organization created successfully.",
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    post=extend_schema(exclude=True)
)
class OrganizationCreateApi(APIView):
    permission_classes = [IsAuthenticatedAndVerified]

    def post(self, request):
        return OrganizationListApi().post(request)


@extend_schema_view(
    get=extend_schema(
        operation_id="organizations_retrieve",
        summary="Get organization details",
        parameters=[ORG_ID_PATH_PARAMETER, FIELDS_PARAMETER],
        responses={200: OrganizationResponseSerializer},
    ),
    patch=extend_schema(
        operation_id="organizations_update_partial",
        summary="Update an organization",
        parameters=[ORG_ID_PATH_PARAMETER],
        request=OrganizationUpdateSerializer,
        responses={200: OrganizationResponseSerializer},
    ),
    put=extend_schema(
        operation_id="organizations_update",
        summary="Replace organization fields",
        parameters=[ORG_ID_PATH_PARAMETER],
        request=OrganizationUpdateSerializer,
        responses={200: OrganizationResponseSerializer},
    ),
    delete=extend_schema(
        operation_id="organizations_delete",
        summary="Soft-delete an organization",
        parameters=[ORG_ID_PATH_PARAMETER],
        responses={200: OrganizationResponseSerializer},
    ),
)
class OrganizationDetailApi(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = OrganizationUpdateSerializer

    def get_object(self, request, id: str) -> Organization:
        _validate_uuid(id)
        try:
            org = Organization.objects.get(id=id)
        except Organization.DoesNotExist as exc:
            raise OrgNotFoundOrDeletedException(
                "The requested organization was not found or has been deleted.",
                extra_details={"id": id},
            ) from exc

        if org.deleted_at:
            raise OrgNotFoundOrDeletedException(
                "The requested organization was not found or has been deleted.",
                extra_details={"id": id},
            )
        if not OrganizationService.can_access_org(request.user, org):
            raise OrgAccessDeniedException(
                "You do not have access to this organization.",
                extra_details={"id": id},
            )
        return org

    def get(self, request, id):
        org = self.get_object(request, id)
        return Response(
            {
                "success": True,
                "data": _apply_field_projection(_organization_payload(org, request.user), request.query_params.get("fields")),
                "message": "Organization retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, id):
        org = self.get_object(request, id)
        if not OrganizationService.can_admin_org(request.user, org):
            raise OrgAccessDeniedException(
                "Insufficient permissions to update organization.",
                extra_details={"required_scope": "organizations:write"},
            )
        serializer = OrganizationUpdateSerializer(org, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        new_slug = serializer.validated_data.get("slug")
        if new_slug and Organization.objects.exclude(id=org.id).filter(slug=new_slug).exists():
            raise ResourceConflictException(
                f"The slug '{new_slug}' is already taken. Please choose another.",
                extra_details={"slug": new_slug},
            )
        org = serializer.save(updated_by=request.user)
        return Response(
            {
                "success": True,
                "data": _organization_payload(org, request.user),
                "message": "Organization updated successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, id):
        return self.patch(request, id)

    def delete(self, request, id):
        org = self.get_object(request, id)
        if not OrganizationService.can_admin_org(request.user, org):
            raise OrgAccessDeniedException(
                "Insufficient permissions to delete organization.",
                extra_details={"required_scope": "organizations:admin"},
            )
        deleted_at = timezone.now()
        org.deleted_at = deleted_at
        org.status = Organization.STATUS_ARCHIVED
        org.updated_by = request.user
        org.save(update_fields=["deleted_at", "status", "updated_by", "updated_at"])
        return Response(
            {
                "success": True,
                "data": _organization_payload(org, request.user),
                "message": "Organization soft-deleted successfully. Data retained for 30 days.",
            },
            status=status.HTTP_200_OK,
        )


def _get_org_or_raise(org_id: str) -> Organization:
    _validate_uuid(org_id)
    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist as exc:
        raise OrgNotFoundOrDeletedException(
            "Organization not found or has been deleted.",
            extra_details={"org_id": org_id},
        ) from exc
    if org.deleted_at:
        raise OrgNotFoundOrDeletedException(
            "Organization not found or has been deleted.",
            extra_details={"org_id": org_id},
        )
    return org


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        operation_id="organization_members_list",
        summary="List organization members",
        parameters=[ORG_PATH_PARAMETER, SEARCH_PARAMETER, STATUS_PARAMETER, ROLE_ID_PARAMETER, sort_parameter("joined_at", "status", "created_at"), ORDER_PARAMETER, PAGE_PARAMETER, LIMIT_PARAMETER, FIELDS_PARAMETER],
        responses={200: OrganizationMembersListResponseSerializer},
    )
)
class OrganizationMembersListApi(APIView):
    permission_classes = [IsAuthenticatedAndVerified]

    ALLOWED_SORT = {"joined_at", "status", "created_at"}

    def get(self, request, org_id):
        org = _get_org_or_raise(org_id)
        if not OrganizationService.can_view_members(request.user, org):
            raise OrgAccessDeniedException(
                "You do not have access to this organization's member list.",
                extra_details={"org_id": org_id},
            )

        qs = OrganizationMembership.objects.select_related("user", "role").filter(organization=org)

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(user__email__icontains=search)
            )

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        role_id = request.query_params.get("role_id")
        if role_id:
            _validate_uuid(role_id)
            qs = qs.filter(role_id=role_id)

        sort_by = request.query_params.get("sort_by", "joined_at")
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
        except (ValueError, TypeError) as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"page": ["Must be an integer."]}) from exc
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
        items = [
            _apply_field_projection(_membership_payload(m), fields_param)
            for m in page_obj.object_list
        ]
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
                "message": "Organization members retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    patch=extend_schema(
        operation_id="organization_member_update",
        summary="Update organization membership",
        parameters=[ORG_PATH_PARAMETER, USER_ID_PATH_PARAMETER],
        request=UpdateMembershipSerializer,
        responses={200: OrganizationMemberResponseSerializer},
    ),
    delete=extend_schema(
        operation_id="organization_member_remove",
        summary="Remove a member from organization",
        parameters=[ORG_PATH_PARAMETER, USER_ID_PATH_PARAMETER],
        responses={200: OrganizationMemberResponseSerializer},
    ),
)
class UpdateMembershipApi(APIView):
    """PATCH → update role/status  |  DELETE → remove member."""

    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = UpdateMembershipSerializer

    def patch(self, request, org_id, user_id):
        org = _get_org_or_raise(org_id)
        if not OrganizationService.can_admin_org(request.user, org):
            raise OrgAccessDeniedException(
                "You do not have permission to update a member in this organization.",
                extra_details={"user_id": user_id, "org_id": org_id},
            )
        membership = OrganizationService.get_member_or_404(org, user_id)
        serializer = UpdateMembershipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = OrganizationService.update_member(membership, serializer.validated_data)
        return Response(
            {
                "success": True,
                "data": _membership_payload(membership, updated_by_id=request.user.id),
                "message": "Member updated successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, org_id, user_id):
        org = _get_org_or_raise(org_id)
        if not OrganizationService.can_admin_org(request.user, org):
            raise OrgAccessDeniedException(
                "Insufficient permissions to remove this member.",
                extra_details={"user_id": user_id, "org_id": org_id},
            )
        membership = OrganizationService.get_member_or_404(org, user_id)
        membership = OrganizationService.remove_member(org, membership)
        payload = _membership_payload(membership, updated_by_id=request.user.id)
        payload["removed_at"] = _fmt(membership.updated_at)
        return Response(
            {
                "success": True,
                "data": payload,
                "message": "Member removed from organization successfully.",
            },
            status=status.HTTP_200_OK,
        )


class RemoveMembershipApi(APIView):
    """Kept for import compatibility; not wired to a URL."""
    pass


# ---------------------------------------------------------------------------
# Invites
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        operation_id="organization_invites_list",
        summary="List organization invites",
        parameters=[ORG_PATH_PARAMETER, SEARCH_PARAMETER, STATUS_PARAMETER, sort_parameter("created_at", "expires_at"), ORDER_PARAMETER, PAGE_PARAMETER, LIMIT_PARAMETER, FIELDS_PARAMETER],
        responses={200: OrganizationInvitesListResponseSerializer},
    ),
    post=extend_schema(
        operation_id="organization_invites_create",
        summary="Invite a member to organization",
        parameters=[ORG_PATH_PARAMETER],
        request=InviteMemberSerializer,
        responses={201: OrganizationInviteResponseSerializer},
    ),
)
class InviteMemberApi(APIView):
    """GET → list invites  |  POST → send invite."""

    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = InviteMemberSerializer

    ALLOWED_SORT = {"created_at", "expires_at"}

    def _require_admin(self, request, org_id, org):
        if not OrganizationService.can_admin_org(request.user, org):
            raise OrgAccessDeniedException(
                "Insufficient permissions to manage invitations for this organization.",
                extra_details={"org_id": org_id},
            )

    def get(self, request, org_id):
        org = _get_org_or_raise(org_id)
        self._require_admin(request, org_id, org)

        qs = OrganizationInvite.objects.select_related("role").filter(organization=org)

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(email__icontains=search)

        status_filter = request.query_params.get("status")
        if status_filter:
            now = timezone.now()
            if status_filter == "pending":
                qs = qs.filter(accepted_at__isnull=True, revoked_at__isnull=True, expires_at__gt=now)
            elif status_filter == "accepted":
                qs = qs.filter(accepted_at__isnull=False)
            elif status_filter == "revoked":
                qs = qs.filter(revoked_at__isnull=False)
            else:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"status": ["Must be one of: pending, accepted, revoked."]})

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
        except (ValueError, TypeError) as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"page": ["Must be an integer."]}) from exc
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
        items = [
            _apply_field_projection(_invite_payload(inv), fields_param)
            for inv in page_obj.object_list
        ]
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
                "message": "Invitations retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, org_id):
        org = _get_org_or_raise(org_id)
        self._require_admin(request, org_id, org)
        serializer = InviteMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _raw_token, invite = OrganizationService.invite_member(
            org=org,
            email=serializer.validated_data["email"],
            role_id=serializer.validated_data["role_id"],
            invited_by=request.user,
        )
        return Response(
            {
                "success": True,
                "data": _invite_payload(invite),
                "message": f"Invitation sent successfully to {invite.email}.",
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    delete=extend_schema(
        operation_id="organization_invites_revoke",
        summary="Revoke an organization invite",
        parameters=[ORG_PATH_PARAMETER, INVITE_ID_PATH_PARAMETER],
        responses={200: InviteRevocationResponseSerializer},
    )
)
class RevokeInviteApi(APIView):
    permission_classes = [IsAuthenticatedAndVerified]

    def delete(self, request, org_id, invite_id):
        org = _get_org_or_raise(org_id)
        if not OrganizationService.can_admin_org(request.user, org):
            raise OrgAccessDeniedException(
                "Insufficient permissions to revoke invitations.",
                extra_details={"org_id": org_id},
            )
        invite = OrganizationService.get_invite_or_404(org, invite_id)
        invite = OrganizationService.revoke_invite(invite)
        return Response(
            {
                "success": True,
                "data": {
                    "id": str(invite.id),
                    "organization_id": str(invite.organization_id),
                    "email": invite.email,
                    "revoked_at": _fmt(invite.revoked_at),
                    "updated_at": _fmt(invite.revoked_at),
                    "updated_by": str(request.user.id),
                    "created_at": _fmt(invite.created_at),
                    "created_by": str(invite.invited_by_user_id),
                },
                "message": "Invitation revoked successfully.",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        operation_id="organization_invites_accept",
        summary="Accept an organization invite",
        request=AcceptInviteSerializer,
        responses={201: AcceptInviteResponseSerializer},
    )
)
class AcceptInviteApi(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = AcceptInviteSerializer

    def post(self, request):
        serializer = AcceptInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership, invite = OrganizationService.accept_invite(
            token_str=serializer.validated_data["token"],
            user=request.user,
        )
        return Response(
            {
                "success": True,
                "data": {
                    "membership": _membership_payload(membership),
                    "invite": {
                        "id": str(invite.id),
                        "accepted_at": _fmt(invite.accepted_at),
                    },
                },
                "message": "Invitation accepted. You are now a member of the organization.",
            },
            status=status.HTTP_201_CREATED,
        )

