from django.urls import path

from apps.organizations.apis import (
    InviteMemberApi,
    OrganizationDetailApi,
    OrganizationListApi,
    OrganizationMembersListApi,
    RemoveMembershipApi,
    RevokeInviteApi,
    UpdateMembershipApi,
)

app_name = "organizations"

urlpatterns = [
    path("", OrganizationListApi.as_view(), name="organization_list"),
    path("<str:id>", OrganizationDetailApi.as_view(), name="organization_detail"),
    path("<str:org_id>/members", OrganizationMembersListApi.as_view(), name="members_list"),
    path("<str:org_id>/members/<str:user_id>", UpdateMembershipApi.as_view(), name="member_detail"),
    path("<str:org_id>/invites", InviteMemberApi.as_view(), name="invites_list"),
    path("<str:org_id>/invites/<str:invite_id>", RevokeInviteApi.as_view(), name="invite_detail"),
]
