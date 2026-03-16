from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("", RedirectView.as_view(url="/health/", permanent=False)),
    path("admin/", admin.site.urls),
    path("health/", include("apps.core.health.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="api-schema"), name="api-redoc"),
    path("api/v1/auth/", include("apps.users.auth_urls")),
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/invites/", include("apps.organizations.invite_urls")),
    path("api/v1/organizations/", include("apps.organizations.urls")),
    path("api/v1/projects/", include("apps.projects.urls")),
    path("api/v1/tasks/", include("apps.tasks.urls")),
    path("api/v1/comments/", include("apps.comments.urls")),
    path("api/v1/attachments/", include("apps.attachments.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/activity-logs/", include("apps.activity_logs.urls")),
    path("api/v1/webhooks/", include("apps.webhooks.urls")),
]
