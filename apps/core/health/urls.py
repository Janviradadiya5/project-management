from django.urls import path
from apps.core.health.apis import HealthApi

urlpatterns = [
    path("", HealthApi.as_view(), name="health"),
]
