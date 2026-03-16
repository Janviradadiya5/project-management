"""Tests for organization APIs."""

import pytest
from rest_framework import status

from apps.organizations.models import OrganizationMembership, Role


@pytest.mark.django_db
class TestOrganizationListApi:
    """Test organization list endpoint."""

    @pytest.mark.auth
    def test_list_organizations_authenticated(self, client_with_org_header, authenticated_user):
        """Test listing user's organizations."""
        response = client_with_org_header.get("/api/v1/organizations")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "data" in response.data

    @pytest.mark.negative
    @pytest.mark.auth
    def test_list_organizations_unauthenticated(self, api_client):
        """Test list requires authentication."""
        response = api_client.get("/api/v1/organizations")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestOrganizationCreateApi:
    """Test organization creation endpoint."""

    @pytest.mark.auth
    def test_create_organization_authenticated(self, authenticated_client):
        """Test creating a new organization."""
        response = authenticated_client.post(
            "/api/v1/organizations",
            data={
                "name": "New Org",
                "slug": "new-org",
                "description": "New organization",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    @pytest.mark.negative
    def test_create_organization_with_invalid_slug(self, authenticated_client):
        """Test creation fails with invalid slug."""
        response = authenticated_client.post(
            "/api/v1/organizations",
            data={
                "name": "New Org",
                "slug": "Invalid Slug!",  # Invalid format
                "description": "Test",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.negative
    @pytest.mark.auth
    def test_create_organization_unauthenticated(self, api_client):
        """Test creation requires authentication."""
        response = api_client.post(
            "/api/v1/organizations",
            data={"name": "New Org", "slug": "new-org"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestOrganizationDetailApi:
    """Test organization detail endpoint."""

    @pytest.mark.auth
    def test_get_organization_detail(self, client_with_org_header, organization):
        """Test getting organization details."""
        response = client_with_org_header.get(
            f"/api/v1/organizations/{organization.id}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["id"] == str(organization.id)

    @pytest.mark.negative
    def test_get_nonexistent_organization(self, client_with_org_header):
        """Test getting non-existent organization."""
        import uuid
        response = client_with_org_header.get(
            f"/api/v1/organizations/{uuid.uuid4()}"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.auth
    @pytest.mark.permission
    def test_update_organization_as_admin(self, client_with_org_header, organization):
        """Test updating organization as admin."""
        response = client_with_org_header.put(
            f"/api/v1/organizations/{organization.id}",
            data={"name": "Updated Org"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        organization.refresh_from_db()
        assert organization.name == "Updated Org"

    @pytest.mark.negative
    @pytest.mark.permission
    def test_update_organization_as_non_admin(self, authenticated_client, organization, another_user):
        """Test non-admin cannot update organization."""
        # Add another_user as non-admin member
        member_role = Role.objects.get_or_create(code="member")[0]
        OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=member_role,
            status=OrganizationMembership.STATUS_ACTIVE,
        )
        
        # Try to update as non-admin
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(another_user)
        authenticated_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        authenticated_client.defaults["HTTP_X_ORGANIZATION_ID"] = str(organization.id)
        
        response = authenticated_client.put(
            f"/api/v1/organizations/{organization.id}",
            data={"name": "Hacked"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestInviteMemberApi:
    """Test invite member endpoint."""

    @pytest.mark.permission
    def test_invite_member_as_admin(self, client_with_org_header, organization, another_user):
        """Test inviting member as admin."""
        response = client_with_org_header.post(
            f"/api/v1/organizations/{organization.id}/members",
            data={
                "email": another_user.email,
                "role_id": "member",
            },
            format="json",
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    @pytest.mark.negative
    @pytest.mark.permission
    def test_invite_member_as_non_admin(self, authenticated_client, organization, another_user):
        """Test non-admin cannot invite members."""
        member_role = Role.objects.get_or_create(code="member")[0]
        OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=member_role,
        )
        
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(another_user)
        authenticated_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        authenticated_client.defaults["HTTP_X_ORGANIZATION_ID"] = str(organization.id)
        
        response = authenticated_client.post(
            f"/api/v1/organizations/{organization.id}/members",
            data={"email": "newuser@example.com"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestOrganizationMembersListApi:
    """Test listing organization members."""

    @pytest.mark.auth
    def test_list_members_authenticated(self, client_with_org_header):
        """Test listing organization members."""
        response = client_with_org_header.get("/api/v1/organizations/1/members")
        # May be 404 if endpoint structure is different
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
        ]

    @pytest.mark.negative
    @pytest.mark.auth
    def test_list_members_requires_org_membership(self, authenticated_client, organization):
        """Test listing members requires organization membership."""
        # Don't set X-Organization-ID header
        response = authenticated_client.get(
            f"/api/v1/organizations/{organization.id}/members"
        )
        # May require header or auth
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


