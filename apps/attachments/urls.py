from django.urls import path

from apps.attachments.apis import (
    AttachmentDetailApi,
)

app_name = "attachments"

urlpatterns = [
    path("<str:id>", AttachmentDetailApi.as_view(), name="attachment_detail"),
]
