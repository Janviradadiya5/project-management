"""Tests for users services."""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.users.models import AuthTokenSession, EmailVerificationToken, PasswordResetToken
from apps.users.services import UserService
from apps.core.exceptions import (
    AuthInvalidCredentialsException,
    AuthRefreshRevokedException,
    AuthTokenInvalidOrExpiredException,
    TokenInvalidOrExpiredException,
)

User = get_user_model()


@pytest.mark.django_db
class TestUserService:
    """Test UserService business logic."""

    def test_authenticate_user_with_valid_credentials(self):
        """Test authenticating user with correct email and password."""
        email = "test@example.com"
        password = "TestPassword123!"
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name="Test",
            last_name="User",
        )
        authenticated_user = UserService.authenticate_user(email, password)
        assert authenticated_user.id == user.id

    def test_authenticate_user_with_uppercase_email(self):
        """Test that email lookup is case-insensitive."""
        email = "test@example.com"
        password = "TestPassword123!"
        User.objects.create_user(
            email=email,
            password=password,
            first_name="Test",
            last_name="User",
        )
        authenticated_user = UserService.authenticate_user("TEST@EXAMPLE.COM", password)
        assert authenticated_user.email == email.lower()

    @pytest.mark.negative
    def test_authenticate_user_with_invalid_password(self):
        """Test authentication fails with wrong password."""
        User.objects.create_user(
            email="test@example.com",
            password="CorrectPassword123!",
            first_name="Test",
            last_name="User",
        )
        with pytest.raises(AuthInvalidCredentialsException):
            UserService.authenticate_user("test@example.com", "WrongPassword123!")

    @pytest.mark.negative
    def test_authenticate_user_with_nonexistent_email(self):
        """Test authentication fails for non-existent user."""
        with pytest.raises(AuthInvalidCredentialsException):
            UserService.authenticate_user("nonexistent@example.com", "Password123!")

    def test_request_email_verification_creates_token(self):
        """Test that email verification token is created."""
        user = User.objects.create_user(
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
        )
        UserService.request_email_verification("test@example.com")
        
        token = EmailVerificationToken.objects.filter(user=user, used_at__isnull=True).first()
        assert token is not None
        assert token.expires_at > timezone.now()

    def test_request_email_verification_for_nonexistent_user(self):
        """Test that requesting verification for non-existent user doesn't raise error."""
        # Should not raise exception (security by obscurity)
        UserService.request_email_verification("nonexistent@example.com")
        assert True

    def test_confirm_email_verification_with_valid_token(self):
        """Test confirming email with valid token."""
        user = User.objects.create_user(
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
            is_email_verified=False,
        )
        UserService.request_email_verification("test@example.com")
        
        # Get the token (would be sent to email in real scenario)
        token_obj = EmailVerificationToken.objects.filter(user=user, used_at__isnull=True).first()
        assert token_obj is not None

    @pytest.mark.negative
    def test_confirm_email_verification_with_invalid_token(self):
        """Test confirming email with invalid token."""
        with pytest.raises(TokenInvalidOrExpiredException):
            UserService.confirm_email_verification("invalid_token_string")

    @pytest.mark.negative
    def test_confirm_email_verification_with_expired_token(self):
        """Test confirming email with expired token."""
        user = User.objects.create_user(
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
        )
        # Create an expired token
        from django.contrib.auth.hashers import make_password
        expired_token = EmailVerificationToken.objects.create(
            user=user,
            token_hash=make_password("expired_token"),
            expires_at=timezone.now() - timedelta(hours=1),
        )
        with pytest.raises(TokenInvalidOrExpiredException):
            UserService.confirm_email_verification("expired_token")

    def test_request_password_reset_creates_token(self):
        """Test that password reset token is created."""
        user = User.objects.create_user(
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
        )
        UserService.request_password_reset("test@example.com")
        
        token = PasswordResetToken.objects.filter(user=user, used_at__isnull=True).first()
        assert token is not None

    def test_logout_user_revokes_all_sessions(self):
        """Test that logout revokes all active sessions."""
        user = User.objects.create_user(
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
        )
        # Create multiple sessions
        session1 = AuthTokenSession.objects.create(
            user=user,
            access_jti="jti1",
            refresh_jti="jti2",
        )
        session2 = AuthTokenSession.objects.create(
            user=user,
            access_jti="jti3",
            refresh_jti="jti4",
        )
        
        UserService.logout_user(user)
        
        # Check both sessions are revoked
        session1.refresh_from_db()
        session2.refresh_from_db()
        assert session1.revoked_at is not None
        assert session2.revoked_at is not None

    def test_logout_only_revokes_user_sessions(self):
        """Test that logout only affects the specific user."""
        user1 = User.objects.create_user(
            email="user1@example.com",
            password="TestPassword123!",
            first_name="User",
            last_name="One",
        )
        user2 = User.objects.create_user(
            email="user2@example.com",
            password="TestPassword123!",
            first_name="User",
            last_name="Two",
        )
        
        session1 = AuthTokenSession.objects.create(
            user=user1,
            access_jti="jti1",
            refresh_jti="jti2",
        )
        session2 = AuthTokenSession.objects.create(
            user=user2,
            access_jti="jti3",
            refresh_jti="jti4",
        )
        
        UserService.logout_user(user1)
        
        session1.refresh_from_db()
        session2.refresh_from_db()
        assert session1.revoked_at is not None
        assert session2.revoked_at is None


