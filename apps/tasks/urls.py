from django.urls import path

from apps.attachments.apis import AttachmentUploadApi
from apps.comments.apis import TaskCommentsListApi
from apps.tasks.apis import (
    TaskCreateApi,
    TaskDetailApi,
    TaskListApi,
)

app_name = "tasks"

urlpatterns = [
    path("", TaskListApi.as_view(), name="task_list"),
    path("<str:id>", TaskDetailApi.as_view(), name="task_detail"),
    path("<str:task_id>/comments", TaskCommentsListApi.as_view(), name="task_comments_create"),
    path("<str:task_id>/attachments", AttachmentUploadApi.as_view(), name="task_attachments"),
]
