import uuid

from django.db import models


class CIEmailField(models.EmailField):
    """Email field backed by PostgreSQL citext type for case-insensitive uniqueness."""

    def db_type(self, connection):
        return "citext"


class BaseModel(models.Model):
    """Abstract base model providing UUID primary key and audit timestamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
