"""Service-layer business logic for app: organizations."""

import hashlib
import secrets
from datetime import timedelta
from uuid import UUID

from django.utils import timezone

from apps.core.exceptions import (
    InviteInvalidOrExpiredException,
    OrgAccessDeniedException,
    OrgNotFoundOrDeletedException,
    ResourceConflictException,
    ResourceNotFoundException,
)
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMembership
from apps.users.models import Role, User


class OrganizationService:
    @staticmethod
    def get_or_create_admin_role() -> Role:
        role, _ = Role.objects.get_or_create(
            code="organization_admin",
            defaults={"name": "Organization Admin", "description": "Administrator for organization"},
        )
        return role

    @staticmethod
    def is_super_admin(user: User) -> bool:
        return bool(getattr(user, "is_superuser", False))

    @staticmethod
    def can_admin_org(user: User, org: Organization) -> bool:
        if OrganizationService.is_super_admin(user):
            return True
        admin_role = OrganizationService.get_or_create_admin_role()
        return OrganizationMembership.objects.filter(
            user=user,
            organization=org,
            role=admin_role,
            status=OrganizationMembership.STATUS_ACTIVE,
        ).exists()

    @staticmethod
    def can_access_org(user: User, org: Organization) -> bool:
        if OrganizationService.is_super_admin(user):
            return True
        return OrganizationMembership.objects.filter(
            user=user,
            organization=org,
            status=OrganizationMembership.STATUS_ACTIVE,
        ).exists()

    @staticmethod
    def can_view_members(user: User, org: Organization) -> bool:
        """super_admin, organization_admin, or project_manager may list members."""
        if OrganizationService.is_super_admin(user):
            return True
        return OrganizationMembership.objects.filter(
            user=user,
            organization=org,
            status=OrganizationMembership.STATUS_ACTIVE,
            role__code__in=["organization_admin", "project_manager"],
        ).exists()

    # ------------------------------------------------------------------
    # Members
    # ------------------------------------------------------------------

    @staticmethod
    def get_member_or_404(org: Organization, user_id) -> OrganizationMembership:
        try:
            uid = UUID(str(user_id))
        except ValueError as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"user_id": ["Not a valid UUID."]}) from exc
        try:
            return OrganizationMembership.objects.select_related("user", "role").get(
                organization=org, user_id=uid
            )
        except OrganizationMembership.DoesNotExist as exc:
            raise ResourceNotFoundException(
                "Member not found in this organization.",
                extra_details={"user_id": str(user_id), "org_id": str(org.id)},
            ) from exc

    @staticmethod
    def update_member(membership: OrganizationMembership, data: dict) -> OrganizationMembership:
        if "role_id" in data:
            membership.role = Role.objects.get(id=data["role_id"])
        if "status" in data:
            membership.status = data["status"]
        membership.save()
        membership.refresh_from_db()
        return membership

    @staticmethod
    def remove_member(org: Organization, membership: OrganizationMembership) -> tuple:
        if membership.user_id == org.owner_user_id:
            raise ResourceConflictException(
                "The organization owner cannot be removed from the organization.",
                extra_details={"user_id": str(membership.user_id), "reason": "owner_cannot_be_removed"},
            )
        membership.status = OrganizationMembership.STATUS_REMOVED
        membership.save(update_fields=["status", "updated_at"])
        return membership

    # ------------------------------------------------------------------
    # Invites
    # ------------------------------------------------------------------

    @staticmethod
    def invite_member(org: Organization, email: str, role_id, invited_by: User) -> tuple:
        """Create an invite. Returns (raw_token, invite)."""
        if OrganizationInvite.objects.filter(
            organization=org,
            email__iexact=email,
            accepted_at__isnull=True,
            revoked_at__isnull=True,
        ).exists():
            raise ResourceConflictException(
                "An active invitation already exists for this email in the organization.",
                extra_details={"email": email, "org_id": str(org.id)},
            )
        role = Role.objects.get(id=role_id)
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = timezone.now() + timedelta(days=7)
        invite = OrganizationInvite.objects.create(
            organization=org,
            email=email.lower(),
            role=role,
            token_hash=token_hash,
            expires_at=expires_at,
            invited_by_user=invited_by,
        )
        return raw_token, invite

    @staticmethod
    def accept_invite(token_str: str, user: User) -> tuple:
        """Validate and accept an invite. Returns (membership, invite)."""
        token_hash = hashlib.sha256(token_str.encode()).hexdigest()
        try:
            invite = OrganizationInvite.objects.select_related("organization", "role").get(
                token_hash=token_hash
            )
        except OrganizationInvite.DoesNotExist as exc:
            raise InviteInvalidOrExpiredException(
                "The invitation token is invalid or has expired.",
                extra_details={"reason": "not_found"},
            ) from exc

        if invite.accepted_at:
            raise ResourceConflictException(
                "This invitation has already been accepted.",
                extra_details={"invite_id": str(invite.id)},
            )
        if invite.revoked_at:
            raise InviteInvalidOrExpiredException(
                "The invitation token is invalid or has expired.",
                extra_details={"reason": "revoked"},
            )
        if invite.expires_at < timezone.now():
            raise InviteInvalidOrExpiredException(
                "The invitation token is invalid or has expired.",
                extra_details={"reason": "expired"},
            )
        if invite.email.lower() != user.email.lower():
            raise OrgAccessDeniedException(
                "You are not authorized to accept this invitation.",
                extra_details={"reason": "email_mismatch"},
            )

        org = invite.organization
        if org.deleted_at:
            raise OrgNotFoundOrDeletedException("Organization not found or has been deleted.")

        now = timezone.now()
        invite.accepted_at = now
        invite.save(update_fields=["accepted_at"])

        membership, created = OrganizationMembership.objects.get_or_create(
            organization=org,
            user=user,
            defaults={
                "role": invite.role,
                "status": OrganizationMembership.STATUS_ACTIVE,
                "joined_at": now,
                "invited_by_user": invite.invited_by_user,
            },
        )
        if not created:
            membership.role = invite.role
            membership.status = OrganizationMembership.STATUS_ACTIVE
            membership.joined_at = now
            membership.save(update_fields=["role", "status", "joined_at", "updated_at"])

        membership.refresh_from_db()
        return membership, invite

    @staticmethod
    def get_invite_or_404(org: Organization, invite_id) -> OrganizationInvite:
        try:
            iid = UUID(str(invite_id))
        except ValueError as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"invite_id": ["Not a valid UUID."]}) from exc
        try:
            return OrganizationInvite.objects.select_related("role").get(id=iid, organization=org)
        except OrganizationInvite.DoesNotExist as exc:
            raise ResourceNotFoundException(
                "Invitation not found.",
                extra_details={"invite_id": str(invite_id)},
            ) from exc

    @staticmethod
    def revoke_invite(invite: OrganizationInvite) -> OrganizationInvite:
        if invite.accepted_at:
            raise ResourceConflictException(
                "This invitation has already been accepted and cannot be revoked.",
                extra_details={
                    "invite_id": str(invite.id),
                    "accepted_at": invite.accepted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
            )
        if invite.revoked_at or invite.expires_at < timezone.now():
            raise InviteInvalidOrExpiredException(
                "Invitation is already revoked or has expired.",
                extra_details={"invite_id": str(invite.id)},
            )
        invite.revoked_at = timezone.now()
        invite.save(update_fields=["revoked_at"])
        return invite

    @staticmethod
    def delete_soft(org: Organization) -> None:
        org.deleted_at = timezone.now()
        org.status = Organization.STATUS_ARCHIVED
        org.save(update_fields=["deleted_at", "status"])

