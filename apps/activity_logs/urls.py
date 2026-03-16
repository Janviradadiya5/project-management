from django.urls import path

from apps.activity_logs.apis import ActivityLogsListApi

app_name = "activity_logs"

urlpatterns = [
    path("", ActivityLogsListApi.as_view(), name="activity_logs_list"),
]
