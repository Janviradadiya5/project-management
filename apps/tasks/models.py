from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel
from apps.projects.models import Project
from apps.users.models import User


class Task(BaseModel):
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
    ]

    STATUS_TODO = "todo"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_DONE = "done"
    STATUS_CHOICES = [
        (STATUS_TODO, "To Do"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_DONE, "Done"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=300)
    description = models.TextField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TODO)
    due_at = models.DateTimeField(null=True, blank=True)
    assignee_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
    )
    created_by_user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="created_tasks",
    )
    updated_by_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_tasks",
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="task_audit_created",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="task_audit_updated",
        db_column="updated_by",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "tasks"
        indexes = [
            models.Index(fields=["project"], name="idx_tasks_project_id"),
            models.Index(
                fields=["assignee_user", "status", "due_at"],
                name="idx_tasks_assignee_status_due",
            ),
            models.Index(
                fields=["project", "status", "priority"],
                name="idx_task_proj_status_pri",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(priority__in=["low", "medium", "high"]),
                name="ck_tasks_priority",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["todo", "in_progress", "done"]),
                name="ck_tasks_status",
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        from django.utils import timezone
        
        # Multi-field validation: status and completed_at consistency
        if self.status == self.STATUS_DONE and not self.completed_at:
            raise ValidationError(
                {"completed_at": "completed_at must be set when status is 'done'."}
            )
        if self.status != self.STATUS_DONE and self.completed_at:
            raise ValidationError(
                {"completed_at": "completed_at must be null when status is not 'done'."}
            )
        
        # Multi-field validation: due_at should not be in the past
        if self.due_at and self.due_at < timezone.now() and self.status != self.STATUS_DONE:
            raise ValidationError(
                {"due_at": "Due date cannot be in the past for incomplete tasks."}
            )
        
        # Multi-field validation: assignee must be a project member
        if self.assignee_user:
            from apps.projects.models import ProjectMember
            if not ProjectMember.objects.filter(
                project=self.project,
                user=self.assignee_user
            ).exists():
                raise ValidationError(
                    {"assignee_user": "Assignee must be a member of the project."}
                )
