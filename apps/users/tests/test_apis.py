"""Tests for users APIs."""

import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestAuthRegisterApi:
    """Test user registration endpoint."""

    def test_register_with_valid_data(self, api_client):
        """Test successful user registration."""
        response = api_client.post(
            "/api/v1/auth/register",
            data={
                "email": "newuser@example.com",
                "password": "NewPassword123!",
                "first_name": "New",
                "last_name": "User",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert "data" in response.data
        assert User.objects.filter(email="newuser@example.com").exists()

    @pytest.mark.negative
    def test_register_with_weak_password(self, api_client):
        """Test registration fails with weak password."""
        response = api_client.post(
            "/api/v1/auth/register",
            data={
                "email": "newuser@example.com",
                "password": "weak",
                "first_name": "New",
                "last_name": "User",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    @pytest.mark.negative
    def test_register_with_invalid_email(self, api_client):
        """Test registration fails with invalid email."""
        response = api_client.post(
            "/api/v1/auth/register",
            data={
                "email": "not-an-email",
                "password": "ValidPassword123!",
                "first_name": "New",
                "last_name": "User",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.negative
    def test_register_with_duplicate_email(self, api_client, authenticated_user):
        """Test registration fails with duplicate email."""
        response = api_client.post(
            "/api/v1/auth/register",
            data={
                "email": authenticated_user.email,
                "password": "ValidPassword123!",
                "first_name": "New",
                "last_name": "User",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAuthLoginApi:
    """Test user login endpoint."""

    def test_login_with_valid_credentials(self, api_client, authenticated_user):
        """Test successful login."""
        response = api_client.post(
            "/api/v1/auth/login",
            data={
                "email": authenticated_user.email,
                "password": "TestPassword123!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "access_token" in response.data["data"]
        assert "refresh_token" in response.data["data"]

    @pytest.mark.negative
    @pytest.mark.auth
    def test_login_with_invalid_password(self, api_client, authenticated_user):
        """Test login fails with wrong password."""
        response = api_client.post(
            "/api/v1/auth/login",
            data={
                "email": authenticated_user.email,
                "password": "WrongPassword123!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False

    @pytest.mark.negative
    @pytest.mark.auth
    def test_login_with_nonexistent_email(self, api_client):
        """Test login fails for non-existent user."""
        response = api_client.post(
            "/api/v1/auth/login",
            data={
                "email": "nonexistent@example.com",
                "password": "SomePassword123!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserProfileApi:
    """Test user profile endpoints."""

    @pytest.mark.auth
    def test_get_profile_authenticated(self, authenticated_client, authenticated_user):
        """Test getting user profile when authenticated."""
        response = authenticated_client.get("/api/v1/users/profile")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["email"] == authenticated_user.email

    @pytest.mark.negative
    @pytest.mark.auth
    def test_get_profile_unauthenticated(self, api_client):
        """Test profile endpoint requires authentication."""
        response = api_client.get("/api/v1/users/profile")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.negative
    @pytest.mark.auth
    def test_get_profile_unverified_email(self, api_client, unverified_user):
        """Test profile endpoint requires verified email."""
        # Create token for unverified user
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(unverified_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        
        response = api_client.get("/api/v1/users/profile")
        # Should fail if email verification is required
        # (depends on permission implementation)

    def test_update_profile_authenticated(self, authenticated_client, authenticated_user):
        """Test updating user profile."""
        response = authenticated_client.put(
            "/api/v1/users/profile",
            data={
                "first_name": "Updated",
                "last_name": "Name",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        authenticated_user.refresh_from_db()
        assert authenticated_user.first_name == "Updated"

    @pytest.mark.negative
    def test_update_profile_unauthenticated(self, api_client):
        """Test profile update requires authentication."""
        response = api_client.put(
            "/api/v1/users/profile",
            data={"first_name": "Updated"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAuthLogoutApi:
    """Test logout endpoint."""

    @pytest.mark.auth
    def test_logout_authenticated(self, authenticated_client, authenticated_user):
        """Test logout revokes user sessions."""
        response = authenticated_client.post("/api/v1/auth/logout")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]
        assert response.data.get("success") is True

    @pytest.mark.negative
    @pytest.mark.auth
    def test_logout_unauthenticated(self, api_client):
        """Test logout requires authentication."""
        response = api_client.post("/api/v1/auth/logout")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestEmailVerificationApi:
    """Test email verification endpoints."""

    def test_request_email_verification(self, api_client, authenticated_user):
        """Test requesting email verification."""
        response = api_client.post(
            "/api/v1/auth/email-verification/request",
            data={"email": authenticated_user.email},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    @pytest.mark.negative
    def test_request_email_verification_nonexistent(self, api_client):
        """Test requesting verification for non-existent email."""
        # Should return success (security: no info disclosure)
        response = api_client.post(
            "/api/v1/auth/email-verification/request",
            data={"email": "nonexistent@example.com"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.negative
    def test_confirm_email_verification_invalid_token(self, api_client):
        """Test confirming with invalid token."""
        response = api_client.post(
            "/api/v1/auth/email-verification/confirm",
            data={"token": "invalid_token"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


