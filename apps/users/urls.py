from django.urls import path

from apps.users.apis import (
    UserGetProfileApi,
    UserUpdateProfileApi,
)

app_name = "users"

urlpatterns = [
    # User profile
    path("me", UserGetProfileApi.as_view(), name="user_profile"),
    path("me/update", UserUpdateProfileApi.as_view(), name="user_profile_update"),
]
