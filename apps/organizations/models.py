import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel, CIEmailField
from apps.users.models import Role, User


class Organization(BaseModel):
    STATUS_ACTIVE = "active"
    STATUS_SUSPENDED = "suspended"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_SUSPENDED, "Suspended"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    owner_user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="owned_organizations",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_organizations",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_organizations",
        db_column="updated_by",
    )

    class Meta:
        db_table = "organizations"
        indexes = [
            models.Index(fields=["owner_user"], name="idx_org_owner_user"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["active", "suspended", "archived"]),
                name="ck_organizations_status",
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        # Multi-field validation: deleted_at and status consistency
        if self.deleted_at and self.status == self.STATUS_ACTIVE:
            raise ValidationError(
                {"status": "Soft-deleted organizations cannot have active status."}
            )
        
        # Multi-field validation: owner must be a member
        if self.owner_user:
            membership_exists = self.memberships.filter(
                user=self.owner_user,
                status=OrganizationMembership.STATUS_ACTIVE
            ).exists()
            if not membership_exists and self.pk:  # Only check for existing orgs
                raise ValidationError(
                    {"owner_user": "Organization owner must be an active member."}
                )

class OrganizationMembership(BaseModel):
    STATUS_INVITED = "invited"
    STATUS_ACTIVE = "active"
    STATUS_SUSPENDED = "suspended"
    STATUS_REMOVED = "removed"
    STATUS_CHOICES = [
        (STATUS_INVITED, "Invited"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_SUSPENDED, "Suspended"),
        (STATUS_REMOVED, "Removed"),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organization_memberships")
    role = models.ForeignKey(Role, on_delete=models.RESTRICT, related_name="memberships")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INVITED)
    joined_at = models.DateTimeField(null=True, blank=True)
    invited_by_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sent_membership_invitations",
    )

    class Meta:
        db_table = "organization_memberships"
        indexes = [
            models.Index(fields=["organization"], name="idx_org_memberships_org_id"),
            models.Index(fields=["user"], name="idx_org_memberships_user_id"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="uq_org_memberships_org_user",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["invited", "active", "suspended", "removed"]),
                name="ck_org_memberships_status",
            ),
        ]

    def __str__(self):
        return f"{self.user} in {self.organization}"


class OrganizationInvite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="invites",
    )
    email = CIEmailField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.RESTRICT, related_name="org_invites")
    token_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    invited_by_user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="sent_org_invites",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_organization_invites",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_organization_invites",
        db_column="updated_by",
    )

    class Meta:
        db_table = "organization_invites"
        indexes = [
            models.Index(
                fields=["organization", "email"],
                condition=models.Q(accepted_at__isnull=True, revoked_at__isnull=True),
                name="idx_orginvite_org_email",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "email"],
                condition=models.Q(accepted_at__isnull=True, revoked_at__isnull=True),
                name="uq_org_invite_active",
            ),
        ]

    def __str__(self):
        return f"Invite({self.email} → {self.organization})"

