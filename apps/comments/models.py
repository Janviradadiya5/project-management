import uuid

from django.db import models

from apps.core.models import BaseModel
from apps.tasks.models import Task
from apps.users.models import User


class Comment(BaseModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author_user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="comments",
    )
    parent_comment = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
    )
    body = models.TextField()
    is_edited = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_comments_audit",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_comments_audit",
        db_column="updated_by",
    )

    class Meta:
        db_table = "comments"
        indexes = [
            models.Index(fields=["task", "created_at"], name="idx_comments_task_created"),
            models.Index(fields=["parent_comment"], name="idx_comments_parent_comment_id"),
        ]

    def __str__(self):
        return f"Comment({self.id}) by {self.author_user_id} on task {self.task_id}"

