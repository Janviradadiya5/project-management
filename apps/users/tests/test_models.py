"""Tests for users models."""

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test User model."""

    def test_user_creation_with_valid_data(self):
        """Test creating a user with valid data."""
        user = User.objects.create_user(
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
        )
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_email_verified is False
        assert user.is_active is True

    def test_user_email_normalization(self):
        """Test that email is normalized to lowercase."""
        user = User.objects.create_user(
            email="TEST@EXAMPLE.COM",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
        )
        assert user.email == "test@example.com"

    def test_user_password_hashing(self):
        """Test that password is hashed, not stored plaintext."""
        password = "TestPassword123!"
        user = User.objects.create_user(
            email="test@example.com",
            password=password,
            first_name="Test",
            last_name="User",
        )
        assert user.password != password
        assert user.check_password(password)

    def test_unique_email_constraint(self):
        """Test that email must be unique."""
        User.objects.create_user(
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
        )
        with pytest.raises(Exception):  # IntegrityError
            User.objects.create_user(
                email="test@example.com",
                password="AnotherPassword123!",
                first_name="Another",
                last_name="User",
            )

    def test_user_str_representation(self):
        """Test __str__ returns email."""
        user = User.objects.create_user(
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
        )
        assert str(user) == "test@example.com"

    @pytest.mark.negative
    def test_user_creation_without_email(self):
        """Test that user cannot be created without email."""
        with pytest.raises(ValueError):
            User.objects.create_user(
                email="",
                password="TestPassword123!",
                first_name="Test",
                last_name="User",
            )

    def test_create_superuser(self):
        """Test creating a superuser."""
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPassword123!",
            first_name="Admin",
            last_name="User",
        )
        assert superuser.is_email_verified is True
        assert superuser.is_active is True

    def test_is_email_verified_default_false(self):
        """Test that is_email_verified defaults to False."""
        user = User.objects.create_user(
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
        )
        assert user.is_email_verified is False

    def test_timestamps_set_on_creation(self):
        """Test that created_at and updated_at are set."""
        user = User.objects.create_user(
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
        )
        assert user.created_at is not None
        assert user.updated_at is not None


