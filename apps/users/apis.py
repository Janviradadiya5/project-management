from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.openapi import success_response_serializer
from apps.core.permissions import IsAuthenticatedAndVerified
from apps.users.serializers import (
    EmailVerificationConfirmSerializer,
    EmailVerificationRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshTokenSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserRegisterSerializer,
    UserUpdateProfileSerializer,
)
from apps.users.services import UserService


def _actor_value(user) -> str:
    return str(user.id) if user else "system"


def _user_base_payload(user) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_email_verified": user.is_email_verified,
        "is_active": user.is_active,
        "is_superuser": bool(getattr(user, "is_superuser", False)),
        "created_at": user.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": user.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "created_by": _actor_value(getattr(user, "created_by", None)),
        "updated_by": _actor_value(getattr(user, "updated_by", None)),
    }


def _session_payload(session) -> dict:
    return {
        "session_id": str(session.id),
        "issued_at": session.issued_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at": session.expires_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


UserAuditSerializer = inline_serializer(
    name="UserAudit",
    fields={
        "id": serializers.CharField(),
        "email": serializers.EmailField(),
        "first_name": serializers.CharField(),
        "last_name": serializers.CharField(),
        "is_email_verified": serializers.BooleanField(),
        "is_active": serializers.BooleanField(),
        "is_superuser": serializers.BooleanField(),
        "created_at": serializers.DateTimeField(),
        "updated_at": serializers.DateTimeField(),
        "created_by": serializers.CharField(),
        "updated_by": serializers.CharField(),
    },
)

SessionSerializer = inline_serializer(
    name="AuthSession",
    fields={
        "session_id": serializers.CharField(),
        "issued_at": serializers.DateTimeField(),
        "expires_at": serializers.DateTimeField(),
    },
)

TokenSerializer = inline_serializer(
    name="AuthTokens",
    fields={
        "access_token": serializers.CharField(),
        "refresh_token": serializers.CharField(),
        "token_type": serializers.CharField(),
        "access_expires_in": serializers.IntegerField(),
        "refresh_expires_in": serializers.IntegerField(),
    },
)

RegisterResponseSerializer = success_response_serializer(
    "AuthRegisterResponse",
    inline_serializer(
        name="AuthRegisterData",
        fields={
            **UserAuditSerializer.fields,
            "verification_sent_to": serializers.EmailField(),
        },
    ),
)

LoginResponseSerializer = success_response_serializer(
    "AuthLoginResponse",
    inline_serializer(
        name="AuthLoginData",
        fields={
            "user": inline_serializer(
                name="AuthLoginUser",
                fields={
                    "id": serializers.CharField(),
                    "email": serializers.EmailField(),
                    "first_name": serializers.CharField(),
                    "last_name": serializers.CharField(),
                    "is_email_verified": serializers.BooleanField(),
                    "is_active": serializers.BooleanField(),
                    "is_superuser": serializers.BooleanField(),
                    "last_login_at": serializers.DateTimeField(allow_null=True),
                },
            ),
            "tokens": TokenSerializer,
            "session": SessionSerializer,
            "created_at": serializers.DateTimeField(),
            "updated_at": serializers.DateTimeField(),
            "created_by": serializers.CharField(),
            "updated_by": serializers.CharField(),
        },
    ),
)

RefreshResponseSerializer = success_response_serializer(
    "AuthRefreshResponse",
    inline_serializer(
        name="AuthRefreshData",
        fields={
            "tokens": TokenSerializer,
            "session": inline_serializer(
                name="AuthRefreshSession",
                fields={
                    **SessionSerializer.fields,
                    "prior_jti": serializers.CharField(),
                },
            ),
            "updated_at": serializers.DateTimeField(),
            "updated_by": serializers.CharField(),
        },
    ),
)

LogoutResponseSerializer = success_response_serializer(
    "AuthLogoutResponse",
    inline_serializer(
        name="AuthLogoutData",
        fields={
            "user_id": serializers.CharField(),
            "revoked_at": serializers.DateTimeField(),
            "updated_at": serializers.DateTimeField(),
            "updated_by": serializers.CharField(),
        },
    ),
)

EmailVerificationRequestResponseSerializer = success_response_serializer(
    "EmailVerificationRequestResponse",
    inline_serializer(
        name="EmailVerificationRequestData",
        fields={
            "email": serializers.EmailField(),
            "message_sent_to": serializers.EmailField(),
            "expires_in": serializers.IntegerField(),
            "updated_at": serializers.DateTimeField(allow_null=True),
            "updated_by": serializers.CharField(),
        },
    ),
)

EmailVerificationConfirmResponseSerializer = success_response_serializer(
    "EmailVerificationConfirmResponse",
    inline_serializer(
        name="EmailVerificationConfirmData",
        fields={
            "id": serializers.CharField(),
            "email": serializers.EmailField(),
            "is_email_verified": serializers.BooleanField(),
            "verified_at": serializers.DateTimeField(),
            "updated_at": serializers.DateTimeField(),
            "updated_by": serializers.CharField(),
        },
    ),
)

PasswordResetRequestResponseSerializer = success_response_serializer(
    "PasswordResetRequestResponse",
    inline_serializer(
        name="PasswordResetRequestData",
        fields={
            "email": serializers.EmailField(),
            "message_sent_to": serializers.EmailField(),
            "expires_in": serializers.IntegerField(),
            "updated_at": serializers.DateTimeField(),
            "updated_by": serializers.CharField(),
        },
    ),
)

PasswordResetConfirmResponseSerializer = success_response_serializer(
    "PasswordResetConfirmResponse",
    inline_serializer(
        name="PasswordResetConfirmData",
        fields={
            "user_id": serializers.CharField(),
            "email": serializers.EmailField(),
            "reset_at": serializers.DateTimeField(),
            "sessions_revoked": serializers.BooleanField(),
            "updated_at": serializers.DateTimeField(),
            "updated_by": serializers.CharField(),
        },
    ),
)

ProfileResponseSerializer = success_response_serializer(
    "UserProfileResponse",
    inline_serializer(
        name="UserProfileData",
        fields={
            **UserAuditSerializer.fields,
        },
    ),
)


@extend_schema_view(
    post=extend_schema(
        operation_id="auth_register",
        summary="Register a new user",
        request=UserRegisterSerializer,
        responses={201: RegisterResponseSerializer},
    )
)
class AuthRegisterApi(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = UserRegisterSerializer

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, verification_sent_to = UserService.register_user(serializer.validated_data)

        data = _user_base_payload(user)
        data["verification_sent_to"] = verification_sent_to

        return Response(
            {
                "success": True,
                "data": data,
                "message": "Registration successful. Please verify your email address.",
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    post=extend_schema(
        operation_id="auth_login",
        summary="Log in a user",
        request=UserLoginSerializer,
        responses={200: LoginResponseSerializer},
    )
)
class AuthLoginApi(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = UserService.authenticate_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        payload = UserService.create_login_payload(user)

        return Response(
            {
                "success": True,
                "data": {
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_email_verified": user.is_email_verified,
                        "is_active": user.is_active,
                        "is_superuser": bool(getattr(user, "is_superuser", False)),
                        "last_login_at": user.last_login.strftime("%Y-%m-%dT%H:%M:%SZ") if user.last_login else None,
                    },
                    "tokens": payload["tokens"],
                    "session": _session_payload(payload["session"]),
                    "created_at": user.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "updated_at": user.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "created_by": _actor_value(getattr(user, "created_by", None)),
                    "updated_by": _actor_value(getattr(user, "updated_by", None)),
                },
                "message": "Login successful.",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        operation_id="auth_refresh",
        summary="Refresh access and refresh tokens",
        request=RefreshTokenSerializer,
        responses={200: RefreshResponseSerializer},
    )
)
class AuthRefreshApi(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = RefreshTokenSerializer

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        access_token, refresh_token, session, prior_jti = UserService.refresh_token(
            user=request.user,
            refresh_token_str=serializer.validated_data["refresh_token"],
        )

        return Response(
            {
                "success": True,
                "data": {
                    "tokens": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "token_type": "Bearer",
                        "access_expires_in": 900,
                        "refresh_expires_in": 604800,
                    },
                    "session": {
                        **_session_payload(session),
                        "prior_jti": prior_jti,
                    },
                    "updated_at": session.issued_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "updated_by": str(request.user.id),
                },
                "message": "Token refreshed successfully.",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        operation_id="auth_logout",
        summary="Revoke active sessions",
        request=RefreshTokenSerializer,
        responses={200: LogoutResponseSerializer},
    )
)
class AuthLogoutApi(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = RefreshTokenSerializer

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        revoked_at = UserService.logout_user(request.user, serializer.validated_data["refresh_token"])
        return Response(
            {
                "success": True,
                "data": {
                    "user_id": str(request.user.id),
                    "revoked_at": revoked_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "updated_at": revoked_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "updated_by": str(request.user.id),
                },
                "message": "Logged out successfully. All active sessions have been revoked.",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        operation_id="auth_email_verification_request",
        summary="Request an email verification link",
        request=EmailVerificationRequestSerializer,
        responses={200: EmailVerificationRequestResponseSerializer},
    )
)
class EmailVerificationRequestApi(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = EmailVerificationRequestSerializer

    def post(self, request):
        serializer = EmailVerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = UserService.request_email_verification(serializer.validated_data["email"])
        return Response(
            {
                "success": True,
                "data": {
                    **data,
                    "updated_at": None,
                    "updated_by": "system",
                },
                "message": "Verification email sent successfully.",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        operation_id="auth_email_verification_confirm",
        summary="Confirm email verification token",
        request=EmailVerificationConfirmSerializer,
        responses={200: EmailVerificationConfirmResponseSerializer},
    )
)
class EmailVerificationConfirmApi(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = EmailVerificationConfirmSerializer

    def post(self, request):
        serializer = EmailVerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, verified_at = UserService.confirm_email_verification(serializer.validated_data["token"])
        return Response(
            {
                "success": True,
                "data": {
                    "id": str(user.id),
                    "email": user.email,
                    "is_email_verified": user.is_email_verified,
                    "verified_at": verified_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "updated_at": verified_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "updated_by": "system",
                },
                "message": "Email address verified successfully. You may now log in.",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        operation_id="auth_password_reset_request",
        summary="Request a password reset link",
        request=PasswordResetRequestSerializer,
        responses={200: PasswordResetRequestResponseSerializer},
    )
)
class PasswordResetRequestApi(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = UserService.request_password_reset(serializer.validated_data["email"])
        return Response(
            {
                "success": True,
                "data": {
                    **data,
                    "updated_at": timezone.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "updated_by": "system",
                },
                "message": "Password reset instructions have been sent to the provided email address.",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        operation_id="auth_password_reset_confirm",
        summary="Reset password with token",
        request=PasswordResetConfirmSerializer,
        responses={200: PasswordResetConfirmResponseSerializer},
    )
)
class PasswordResetConfirmApi(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, reset_at = UserService.confirm_password_reset(
            serializer.validated_data["token"],
            serializer.validated_data["new_password"],
        )
        return Response(
            {
                "success": True,
                "data": {
                    "user_id": str(user.id),
                    "email": user.email,
                    "reset_at": reset_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "sessions_revoked": True,
                    "updated_at": reset_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "updated_by": str(user.id),
                },
                "message": "Password reset successfully. All active sessions have been revoked.",
            },
            status=status.HTTP_200_OK,
        )


class UserGetProfileApi(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = UserProfileSerializer

    @extend_schema(
        operation_id="users_me_retrieve",
        summary="Get current user profile",
        responses={200: ProfileResponseSerializer},
    )
    def get(self, request):
        return Response(
            {
                "success": True,
                "data": _user_base_payload(request.user),
                "message": "User profile retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )


class UserUpdateProfileApi(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = UserUpdateProfileSerializer

    @extend_schema(
        operation_id="users_me_update",
        summary="Update current user profile",
        request=UserUpdateProfileSerializer,
        responses={200: ProfileResponseSerializer},
    )
    def patch(self, request):
        serializer = UserUpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(updated_by=request.user)
        return Response(
            {
                "success": True,
                "data": _user_base_payload(user),
                "message": "User profile updated successfully.",
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="users_me_replace",
        summary="Replace current user profile fields",
        request=UserUpdateProfileSerializer,
        responses={200: ProfileResponseSerializer},
    )
    def put(self, request):
        return self.patch(request)
