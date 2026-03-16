"""Tests for organization services."""

import pytest
from django.core.exceptions import ValidationError

from apps.organizations.models import Organization, OrganizationMembership, Role
from apps.organizations.services import OrganizationService
from apps.users.models import User
from apps.core.exceptions import PermissionDeniedException


@pytest.mark.django_db
class TestOrganizationService:
    """Test OrganizationService business logic."""

    def test_can_admin_org_returns_true_for_admin(self, organization, authenticated_user):
        """Test that organization admin can administer org."""
        admin_role = Role.objects.get_or_create(code="organization_admin")[0]
        OrganizationMembership.objects.filter(
            organization=organization,
            user=authenticated_user,
        ).update(role=admin_role)
        
        can_admin = OrganizationService.can_admin_org(authenticated_user, organization)
        assert can_admin is True

    @pytest.mark.negative
    @pytest.mark.permission
    def test_can_admin_org_returns_false_for_non_admin(self, organization, another_user):
        """Test that non-admin cannot administer org."""
        member_role = Role.objects.get_or_create(code="member")[0]
        OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=member_role,
            status=OrganizationMembership.STATUS_ACTIVE,
        )
        
        can_admin = OrganizationService.can_admin_org(another_user, organization)
        assert can_admin is False

    @pytest.mark.negative
    @pytest.mark.permission
    def test_can_admin_org_returns_false_non_member(self, organization, another_user):
        """Test that non-member cannot administer org."""
        can_admin = OrganizationService.can_admin_org(another_user, organization)
        assert can_admin is False

    def test_can_view_members_returns_true_for_member(self, organization, authenticated_user):
        """Test that member can view organization members."""
        can_view = OrganizationService.can_view_members(authenticated_user, organization)
        assert can_view is True

    @pytest.mark.negative
    def test_can_view_members_returns_false_non_member(self, organization, another_user):
        """Test that non-member cannot view organization members."""
        can_view = OrganizationService.can_view_members(another_user, organization)
        assert can_view is False

    def test_invite_member_creates_membership(self, organization, authenticated_user, another_user):
        """Test inviting a member to organization."""
        admin_role = Role.objects.get_or_create(code="organization_admin")[0]
        member_role = Role.objects.get_or_create(code="member")[0]
        
        OrganizationService.invite_member(
            organization,
            another_user.email,
            member_role.code,
            authenticated_user,
        )
        
        membership = OrganizationMembership.objects.get(
            organization=organization,
            user=another_user,
        )
        assert membership.role == member_role

    def test_accept_invite_activates_membership(self, organization, another_user):
        """Test accepting organization invite."""
        member_role = Role.objects.get_or_create(code="member")[0]
        membership = OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=member_role,
            status=OrganizationMembership.STATUS_INVITED,
        )
        
        OrganizationService.accept_invite(membership)
        membership.refresh_from_db()
        
        assert membership.status == OrganizationMembership.STATUS_ACTIVE

    def test_update_membership_role(self, organization, another_user, authenticated_user):
        """Test updating member role."""
        member_role = Role.objects.get_or_create(code="member")[0]
        admin_role = Role.objects.get_or_create(code="admin")[0]
        
        membership = OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=member_role,
        )
        
        OrganizationService.update_membership(
            membership,
            {"role_id": str(admin_role.id)},
            authenticated_user,
        )
        
        membership.refresh_from_db()
        assert membership.role == admin_role

    def test_delete_soft_organization(self, organization):
        """Test soft delete sets deleted_at."""
        org_id = organization.id
        OrganizationService.delete_soft(organization)
        
        org = Organization.objects.get(id=org_id)
        assert org.deleted_at is not None
        assert org.status == "archived"


