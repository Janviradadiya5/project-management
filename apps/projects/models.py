import uuid

from django.db import models

from apps.core.models import BaseModel
from apps.organizations.models import Organization
from apps.users.models import User


class Project(BaseModel):
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    deadline_at = models.DateTimeField(null=True, blank=True)
    created_by_user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="created_projects",
    )
    updated_by_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_projects",
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="project_audit_created",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="project_audit_updated",
        db_column="updated_by",
    )
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "projects"
        indexes = [
            models.Index(fields=["organization"], name="idx_projects_org_id"),
            models.Index(
                fields=["organization", "status", "deadline_at"],
                name="idx_project_org_status_dl",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["active", "completed", "archived"]),
                name="ck_projects_status",
            ),
            models.UniqueConstraint(
                fields=["organization", "name"],
                condition=models.Q(deleted_at__isnull=True),
                name="uq_projects_org_name_active",
            ),
        ]

    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    ROLE_MANAGER = "manager"
    ROLE_CONTRIBUTOR = "contributor"
    ROLE_VIEWER = "viewer"
    ROLE_CHOICES = [
        (ROLE_MANAGER, "Manager"),
        (ROLE_CONTRIBUTOR, "Contributor"),
        (ROLE_VIEWER, "Viewer"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project_memberships")
    project_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CONTRIBUTOR)
    added_by_user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="added_project_members",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_project_members",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_project_members",
        db_column="updated_by",
    )

    class Meta:
        db_table = "project_members"
        indexes = [
            models.Index(fields=["project"], name="idx_project_members_project_id"),
            models.Index(fields=["user"], name="idx_project_members_user_id"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="uq_project_members_project_user",
            ),
            models.CheckConstraint(
                condition=models.Q(project_role__in=["manager", "contributor", "viewer"]),
                name="ck_project_members_role",
            ),
        ]

    def __str__(self):
        return f"{self.user} on {self.project} ({self.project_role})"

