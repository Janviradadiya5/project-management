from django.urls import path

from apps.organizations.apis import AcceptInviteApi

urlpatterns = [
    path("accept", AcceptInviteApi.as_view(), name="accept_invite"),
]
