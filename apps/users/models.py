import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models

from apps.core.models import BaseModel, CIEmailField


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        user = self.model(email=email.lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_email_verified", True)
        return self.create_user(email, password, **extra_fields)


class Role(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_roles",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_roles",
        db_column="updated_by",
    )

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.name


class User(BaseModel, AbstractBaseUser):
    # Override AbstractBaseUser.password to match DB column name
    password = models.CharField(max_length=255, db_column="password_hash")
    # Override AbstractBaseUser.last_login to match DB column name
    last_login = models.DateTimeField(null=True, blank=True, db_column="last_login_at")

    email = CIEmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_users",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_users",
        db_column="updated_by",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email"], name="idx_users_email"),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class EmailVerificationToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )
    token_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_email_verification_tokens",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_email_verification_tokens",
        db_column="updated_by",
    )

    class Meta:
        db_table = "email_verification_tokens"
        indexes = [
            models.Index(fields=["user"], name="idx_email_verif_tokens_user_id"),
        ]

    def __str__(self):
        return f"EmailVerificationToken(user={self.user_id})"


class PasswordResetToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_password_reset_tokens",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_password_reset_tokens",
        db_column="updated_by",
    )

    class Meta:
        db_table = "password_reset_tokens"
        indexes = [
            models.Index(fields=["user"], name="idx_pwd_reset_tokens_user_id"),
        ]

    def __str__(self):
        return f"PasswordResetToken(user={self.user_id})"


class AuthTokenSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="auth_token_sessions",
    )
    refresh_jti = models.CharField(max_length=255)
    issued_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_auth_token_sessions",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_auth_token_sessions",
        db_column="updated_by",
    )

    class Meta:
        db_table = "auth_token_sessions"
        indexes = [
            models.Index(fields=["user"], name="idx_auth_sessions_user_id"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["refresh_jti"],
                name="uq_auth_sessions_refresh_jti",
            ),
        ]

    def __str__(self):
        return f"AuthTokenSession(user={self.user_id}, jti={self.refresh_jti[:8]})"

