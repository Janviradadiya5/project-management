"""Tests for Organization and OrganizationMembership models."""

import pytest
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

from apps.organizations.models import Organization, OrganizationMembership, Role
from apps.users.models import User


@pytest.mark.django_db
class TestOrganizationModel:
    """Test Organization model."""

    def test_create_organization_with_valid_data(self, authenticated_user):
        """Test creating organization with valid data."""
        org = Organization.objects.create(
            name="Test Org",
            slug="test-org",
            owner_user=authenticated_user,
            status="active",
        )
        assert org.name == "Test Org"
        assert org.slug == "test-org"
        assert org.owner_user == authenticated_user
        assert org.status == "active"
        assert org.deleted_at is None

    def test_organization_str_representation(self, organization):
        """Test __str__ returns organization name."""
        assert str(organization) == organization.name

    def test_organization_timestamps(self, authenticated_user):
        """Test created_at and updated_at are set."""
        org = Organization.objects.create(
            name="Test Org",
            slug="test-org",
            owner_user=authenticated_user,
        )
        assert org.created_at is not None
        assert org.updated_at is not None

    def test_organization_unique_slug(self, organization, authenticated_user):
        """Test that slug must be unique."""
        with pytest.raises(IntegrityError):
            Organization.objects.create(
                name="Another Org",
                slug=organization.slug,
                owner_user=authenticated_user,
            )

    def test_soft_delete_organization(self, organization):
        """Test soft delete sets deleted_at timestamp."""
        org_id = organization.id
        organization.deleted_at = timezone.now()
        organization.status = "archived"
        organization.save()
        
        org = Organization.objects.get(id=org_id)
        assert org.deleted_at is not None
        assert org.status == "archived"

    def test_organization_clean_validation(self, authenticated_user):
        """Test clean() validation for organization."""
        org = Organization(
            name="Test Org",
            slug="test-org",
            owner_user=authenticated_user,
            status="archived",
            deleted_at=None,
        )
        with pytest.raises(Exception):  # ValidationError
            org.full_clean()

    def test_organization_optional_fields(self, authenticated_user):
        """Test optional fields (description)."""
        org = Organization.objects.create(
            name="Test Org",
            slug="test-org",
            owner_user=authenticated_user,
            description="Test description",
        )
        assert org.description == "Test description"

    def test_organization_status_choices(self, authenticated_user):
        """Test organization status is one of valid choices."""
        org = Organization.objects.create(
            name="Test Org",
            slug="test-org",
            owner_user=authenticated_user,
            status="active",
        )
        assert org.status in ["active", "archived"]


@pytest.mark.django_db
class TestOrganizationMembershipModel:
    """Test OrganizationMembership model."""

    def test_create_membership_with_valid_data(self, organization, another_user):
        """Test creating organization membership."""
        role = Role.objects.get_or_create(code="member")[0]
        membership = OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=role,
            status=OrganizationMembership.STATUS_ACTIVE,
        )
        assert membership.organization == organization
        assert membership.user == another_user
        assert membership.status == OrganizationMembership.STATUS_ACTIVE

    def test_membership_str_representation(self, organization, another_user):
        """Test __str__ returns user and organization."""
        role = Role.objects.get_or_create(code="member")[0]
        membership = OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=role,
        )
        assert str(membership) == f"{another_user} in {organization.name}"

    def test_membership_unique_constraint(self, organization, another_user):
        """Test that user can only have one membership per org."""
        role = Role.objects.get_or_create(code="member")[0]
        OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=role,
        )
        with pytest.raises(IntegrityError):
            OrganizationMembership.objects.create(
                organization=organization,
                user=another_user,
                role=role,
            )

    def test_membership_status_choices(self, organization, another_user):
        """Test membership status is one of valid choices."""
        role = Role.objects.get_or_create(code="member")[0]
        membership = OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=role,
            status=OrganizationMembership.STATUS_INVITED,
        )
        assert membership.status in [
            OrganizationMembership.STATUS_ACTIVE,
            OrganizationMembership.STATUS_INVITED,
            OrganizationMembership.STATUS_SUSPENDED,
            OrganizationMembership.STATUS_REMOVED,
        ]

    def test_membership_timestamps(self, organization, another_user):
        """Test created_at is set on membership creation."""
        role = Role.objects.get_or_create(code="member")[0]
        membership = OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=role,
        )
        assert membership.created_at is not None

    def test_cascade_delete_membership_on_user_delete(self, organization, another_user):
        """Test that memberships are deleted when user is deleted."""
        role = Role.objects.get_or_create(code="member")[0]
        membership = OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=role,
        )
        membership_id = membership.id
        another_user.delete()
        
        with pytest.raises(OrganizationMembership.DoesNotExist):
            OrganizationMembership.objects.get(id=membership_id)

    def test_membership_invited_status(self, organization, another_user):
        """Test member can be invited (not active)."""
        role = Role.objects.get_or_create(code="member")[0]
        membership = OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=role,
            status=OrganizationMembership.STATUS_INVITED,
        )
        assert membership.status == OrganizationMembership.STATUS_INVITED

    def test_membership_multiple_roles(self, organization, authenticated_user, another_user):
        """Test multiple users can have different roles."""
        admin_role = Role.objects.get_or_create(code="admin")[0]
        member_role = Role.objects.get_or_create(code="member")[0]
        
        admin_membership = OrganizationMembership.objects.create(
            organization=organization,
            user=authenticated_user,
            role=admin_role,
        )
        member_membership = OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=member_role,
        )
        
        assert admin_membership.role == admin_role
        assert member_membership.role == member_role


@pytest.mark.django_db
class TestRoleModel:
    """Test Role model."""

    def test_create_role_with_valid_data(self):
        """Test creating a role."""
        role = Role.objects.create(
            code="custom_role",
            name="Custom Role",
            description="A custom role for testing",
        )
        assert role.code == "custom_role"
        assert role.name == "Custom Role"

    def test_unique_role_code(self):
        """Test that role code must be unique."""
        Role.objects.create(code="admin", name="Administrator")
        with pytest.raises(IntegrityError):
            Role.objects.create(code="admin", name="Another Admin")

    def test_role_str_representation(self):
        """Test __str__ returns role name."""
        role = Role.objects.create(code="viewer", name="Viewer")
        assert str(role) == "Viewer"


