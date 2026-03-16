from django.urls import path

from apps.projects.apis import (
    ProjectAddMemberApi,
    ProjectCreateApi,
    ProjectDetailApi,
    ProjectListApi,
    ProjectRemoveMemberApi,
)

app_name = "projects"

urlpatterns = [
    path("", ProjectListApi.as_view(), name="project_list"),
    path("<str:id>", ProjectDetailApi.as_view(), name="project_detail"),
    path("<str:id>/members", ProjectAddMemberApi.as_view(), name="project_add_member"),
    path("<str:id>/members/<str:project_member_id>", ProjectRemoveMemberApi.as_view(), name="project_remove_member"),
]
