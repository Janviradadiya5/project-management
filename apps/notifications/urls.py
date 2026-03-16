from django.urls import path

from apps.notifications.apis import (
    NotificationsListApi,
    NotificationMarkAsReadApi,
)

app_name = "notifications"

urlpatterns = [
    path("", NotificationsListApi.as_view(), name="notifications_list"),
    path("<str:id>/read", NotificationMarkAsReadApi.as_view(), name="notification_mark_read"),
]
