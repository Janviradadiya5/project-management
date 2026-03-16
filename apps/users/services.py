"""Service-layer business logic for app: users."""

import os
import secrets
from datetime import datetime, timedelta, timezone
import logging

from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone as django_timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions import (
    AuthEmailNotVerifiedException,
    AuthInvalidCredentialsException,
    AuthRefreshRevokedException,
    AuthTokenInvalidOrExpiredException,
    ResourceConflictException,
)
from apps.users.models import AuthTokenSession, EmailVerificationToken, PasswordResetToken, User


logger = logging.getLogger(__name__)


class UserService:
    PASSWORD_RESET_TTL_SECONDS = 3600
    EMAIL_VERIFICATION_TTL_HOURS = 24

    @staticmethod
    def _create_email_verification_token(user: User) -> tuple[str, EmailVerificationToken]:
        token = secrets.token_urlsafe(32)
        token_hash = make_password(token)
        token_obj = EmailVerificationToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=django_timezone.now() + timedelta(hours=UserService.EMAIL_VERIFICATION_TTL_HOURS),
        )
        return token, token_obj

    @staticmethod
    def _frontend_base_url() -> str:
        return os.getenv("APP_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

    @staticmethod
    def _safe_send_mail(*, subject: str, message: str, to_email: str) -> None:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[to_email],
                fail_silently=False,
            )
        except Exception:
            # Do not break auth flows if email provider is temporarily unavailable.
            logger.exception("Failed to send email", extra={"recipient": to_email, "subject": subject})

    @staticmethod
    def _send_email_verification_message(user: User, token: str) -> None:
        verify_link = f"{UserService._frontend_base_url()}/verify-email?token={token}"
        message = (
            "Welcome! Please verify your email address.\n\n"
            f"Verification token: {token}\n"
            f"Verification link: {verify_link}\n\n"
            "This token expires in 24 hours."
        )
        UserService._safe_send_mail(
            subject="Verify your email address",
            message=message,
            to_email=user.email,
        )

    @staticmethod
    def _send_password_reset_message(user: User, token: str) -> None:
        reset_link = f"{UserService._frontend_base_url()}/reset-password?token={token}"
        message = (
            "We received a request to reset your password.\n\n"
            f"Reset token: {token}\n"
            f"Reset link: {reset_link}\n\n"
            "This token expires in 1 hour."
        )
        UserService._safe_send_mail(
            subject="Password reset request",
            message=message,
            to_email=user.email,
        )

    @staticmethod
    def _create_password_reset_token(user: User) -> tuple[str, PasswordResetToken]:
        token = secrets.token_urlsafe(32)
        token_hash = make_password(token)
        token_obj = PasswordResetToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=django_timezone.now() + timedelta(seconds=UserService.PASSWORD_RESET_TTL_SECONDS),
        )
        return token, token_obj

    @staticmethod
    def _token_expiry_datetime(token: RefreshToken) -> datetime:
        return datetime.fromtimestamp(int(token["exp"]), tz=timezone.utc)

    @staticmethod
    def _issue_session_tokens(user: User) -> tuple[str, str, AuthTokenSession]:
        now = django_timezone.now()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        session = AuthTokenSession.objects.create(
            user=user,
            refresh_jti=str(refresh["jti"]),
            issued_at=now,
            expires_at=UserService._token_expiry_datetime(refresh),
        )
        return access_token, refresh_token, session

    @staticmethod
    def _match_email_verification_token(token: str) -> EmailVerificationToken | None:
        for token_obj in EmailVerificationToken.objects.select_related("user"):
            if check_password(token, token_obj.token_hash):
                return token_obj
        return None

    @staticmethod
    def _match_password_reset_token(token: str) -> PasswordResetToken | None:
        for token_obj in PasswordResetToken.objects.select_related("user"):
            if check_password(token, token_obj.token_hash):
                return token_obj
        return None

    @staticmethod
    def register_user(validated_data: dict) -> tuple[User, str]:
        email = validated_data["email"].lower()
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            if existing_user.is_email_verified:
                raise ResourceConflictException("An account with this email address already exists.")
            raise AuthEmailNotVerifiedException("Account exists but email is not yet verified.")

        user = User.objects.create_user(**validated_data)
        token, _ = UserService._create_email_verification_token(user)
        UserService._send_email_verification_message(user, token)
        return user, user.email

    @staticmethod
    def authenticate_user(email: str, password: str) -> User:
        """Authenticate user by email and password."""
        try:
            user = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            raise AuthInvalidCredentialsException()
        if not check_password(password, user.password):
            raise AuthInvalidCredentialsException()
        if not user.is_email_verified:
            raise AuthEmailNotVerifiedException("Email address not verified. Check your inbox.")
        user.last_login = django_timezone.now()
        user.save(update_fields=["last_login"])
        return user

    @staticmethod
    def create_login_payload(user: User) -> dict:
        access_token, refresh_token, session = UserService._issue_session_tokens(user)
        return {
            "user": user,
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "access_expires_in": 900,
                "refresh_expires_in": 604800,
            },
            "session": session,
        }

    @staticmethod
    def refresh_token(user: User, refresh_token_str: str) -> tuple[str, str, AuthTokenSession, str]:
        """Refresh access token using refresh token and rotate session."""
        try:
            refresh = RefreshToken(refresh_token_str)
        except TokenError:
            raise AuthTokenInvalidOrExpiredException()

        jti = str(refresh.get("jti"))
        try:
            session = AuthTokenSession.objects.get(refresh_jti=jti, user=user)
        except AuthTokenSession.DoesNotExist:
            raise AuthRefreshRevokedException()

        if session.revoked_at:
            raise AuthRefreshRevokedException()

        prior_jti = session.refresh_jti
        session.revoked_at = django_timezone.now()
        session.revoked_reason = "Refresh token rotated"
        session.save(update_fields=["revoked_at", "revoked_reason"])

        new_access_token, new_refresh_token, new_session = UserService._issue_session_tokens(user)
        return new_access_token, new_refresh_token, new_session, prior_jti

    @staticmethod
    def logout_user(user: User, refresh_token_str: str) -> datetime:
        """Validate refresh token and revoke all active sessions for user."""
        try:
            refresh = RefreshToken(refresh_token_str)
        except TokenError:
            raise AuthTokenInvalidOrExpiredException()

        jti = str(refresh.get("jti"))
        session = AuthTokenSession.objects.filter(refresh_jti=jti, user=user).first()
        if session is None or session.revoked_at:
            raise AuthRefreshRevokedException()

        revoked_at = django_timezone.now()
        AuthTokenSession.objects.filter(user=user, revoked_at__isnull=True).update(
            revoked_at=revoked_at,
            revoked_reason="User logout",
        )
        return revoked_at

    @staticmethod
    def request_email_verification(email: str) -> dict:
        """Create email verification token."""
        try:
            user = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            return {"email": email.lower(), "message_sent_to": email.lower(), "expires_in": 86400}

        token, _ = UserService._create_email_verification_token(user)
        UserService._send_email_verification_message(user, token)
        return {"email": user.email, "message_sent_to": user.email, "expires_in": 86400}

    @staticmethod
    def confirm_email_verification(token: str) -> tuple[User, datetime]:
        """Verify email using token."""
        token_obj = UserService._match_email_verification_token(token)
        if token_obj is None:
            raise AuthTokenInvalidOrExpiredException("The verification token is invalid or has expired. Please request a new one.")

        if token_obj.used_at:
            raise ResourceConflictException("Email address has already been verified.")
        if token_obj.expires_at <= django_timezone.now():
            raise AuthTokenInvalidOrExpiredException("The verification token is invalid or has expired. Please request a new one.")
        if token_obj.user.is_email_verified:
            raise ResourceConflictException("Email address has already been verified.")

        verified_at = django_timezone.now()
        token_obj.user.is_email_verified = True
        token_obj.user.save(update_fields=["is_email_verified"])
        token_obj.used_at = verified_at
        token_obj.save(update_fields=["used_at"])
        return token_obj.user, verified_at

    @staticmethod
    def request_password_reset(email: str) -> dict:
        """Create password reset token."""
        try:
            user = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            return {"email": email.lower(), "message_sent_to": email.lower(), "expires_in": UserService.PASSWORD_RESET_TTL_SECONDS}

        if not user.is_email_verified:
            raise AuthEmailNotVerifiedException("Email address has not been verified.")

        if PasswordResetToken.objects.filter(
            user=user,
            used_at__isnull=True,
            expires_at__gt=django_timezone.now(),
        ).exists():
            raise ResourceConflictException("A pending reset request already exists.")

        token, _ = UserService._create_password_reset_token(user)
        UserService._send_password_reset_message(user, token)
        return {
            "email": user.email,
            "message_sent_to": user.email,
            "expires_in": UserService.PASSWORD_RESET_TTL_SECONDS,
        }

    @staticmethod
    def confirm_password_reset(token: str, new_password: str) -> tuple[User, datetime]:
        """Reset password using token."""
        token_obj = UserService._match_password_reset_token(token)
        if token_obj is None:
            raise AuthTokenInvalidOrExpiredException("The password reset token is invalid or has expired. Please request a new one.")

        if token_obj.used_at:
            raise ResourceConflictException("This reset token has already been used.")
        if token_obj.expires_at <= django_timezone.now():
            raise AuthTokenInvalidOrExpiredException("The password reset token is invalid or has expired. Please request a new one.")
        if not token_obj.user.is_email_verified:
            raise AuthEmailNotVerifiedException("Account email address is not verified.")

        reset_at = django_timezone.now()
        token_obj.user.password = make_password(new_password)
        token_obj.user.save(update_fields=["password"])
        token_obj.used_at = reset_at
        token_obj.save(update_fields=["used_at"])
        AuthTokenSession.objects.filter(user=token_obj.user, revoked_at__isnull=True).update(
            revoked_at=reset_at,
            revoked_reason="Password reset",
        )
        return token_obj.user, reset_at
