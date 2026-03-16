from django.urls import path

from apps.comments.apis import (
    CommentUpdateApi,
)

app_name = "comments"

urlpatterns = [
    path("<str:id>", CommentUpdateApi.as_view(), name="comment_detail"),
]
