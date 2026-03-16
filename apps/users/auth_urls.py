from django.urls import path

from apps.users.apis import (
    AuthLoginApi,
    AuthLogoutApi,
    AuthRefreshApi,
    AuthRegisterApi,
    EmailVerificationConfirmApi,
    EmailVerificationRequestApi,
    PasswordResetConfirmApi,
    PasswordResetRequestApi,
)

app_name = "auth"

urlpatterns = [
    path("register", AuthRegisterApi.as_view(), name="register"),
    path("verify-email", EmailVerificationConfirmApi.as_view(), name="verify_email"),
    path("login", AuthLoginApi.as_view(), name="login"),
    path("logout", AuthLogoutApi.as_view(), name="logout"),
    path("token/refresh", AuthRefreshApi.as_view(), name="token_refresh"),
    path("password-reset/request", PasswordResetRequestApi.as_view(), name="password_reset_request"),
    path("password-reset/confirm", PasswordResetConfirmApi.as_view(), name="password_reset_confirm"),
    path("email-verification/request", EmailVerificationRequestApi.as_view(), name="email_verification_request"),
]