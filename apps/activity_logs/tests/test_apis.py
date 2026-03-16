"""Tests for ActivityLog REST API endpoints."""

import pytest
import uuid
from rest_framework import status

from apps.activity_logs.models import ActivityLog


@pytest.mark.django_db
class TestActivityLogsListApi:
    """Test cases for ActivityLogs list endpoint."""

    @pytest.mark.auth
    def test_list_activity_logs_authentication_required(self, api_client, organization):
        """Test that authentication is required."""
        response = api_client.get(
            "/api/v1/activity-logs/",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.permission
    def test_list_activity_logs_requires_admin(self, authenticated_client, organization, authenticated_user, another_user):
        """Test that only admins can list activity logs."""
        from apps.organizations.models import OrganizationMembership, Role
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        # Make another_user a non-admin member
        member_role = Role.objects.get_or_create(code="organization_member")[0]
        OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=member_role,
            status=OrganizationMembership.STATUS_ACTIVE,
        )
        
        client = APIClient()
        refresh = RefreshToken.for_user(another_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        response = client.get(
            "/api/v1/activity-logs/",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_activity_logs_success(self, authenticated_client, organization, authenticated_user):
        """Test successfully listing activity logs."""
        ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="task_created",
            target_type="Task",
            target_id=uuid.uuid4(),
        )
        ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="task_updated",
            target_type="Task",
            target_id=uuid.uuid4(),
        )
        
        response = authenticated_client.get(
            "/api/v1/activity-logs/",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_list_activity_logs_pagination(self, authenticated_client, organization, authenticated_user):
        """Test activity log list pagination."""
        for i in range(15):
            ActivityLog.objects.create(
                organization=organization,
                actor_user=authenticated_user,
                event_type=f"event{i}",
                target_type="Resource",
                target_id=uuid.uuid4(),
            )
        
        response = authenticated_client.get(
            "/api/v1/activity-logs/?page=1",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert "next" in response.data
        assert response.data["count"] == 15

    def test_list_activity_logs_filter_by_event_type(self, authenticated_client, organization, authenticated_user):
        """Test filtering activity logs by event type."""
        ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="task_created",
            target_type="Task",
            target_id=uuid.uuid4(),
        )
        ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="comment_added",
            target_type="Comment",
            target_id=uuid.uuid4(),
        )
        
        response = authenticated_client.get(
            "/api/v1/activity-logs/?event_type=task_created",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["event_type"] == "task_created"

    def test_list_activity_logs_filter_by_actor(self, authenticated_client, organization, authenticated_user, another_user):
        """Test filtering activity logs by actor."""
        from apps.organizations.models import OrganizationMembership, Role
        
        member_role = Role.objects.get_or_create(code="organization_member")[0]
        OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=member_role,
            status=OrganizationMembership.STATUS_ACTIVE,
        )
        
        ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="event1",
            target_type="Task",
            target_id=uuid.uuid4(),
        )
        ActivityLog.objects.create(
            organization=organization,
            actor_user=another_user,
            event_type="event2",
            target_type="Task",
            target_id=uuid.uuid4(),
        )
        
        response = authenticated_client.get(
            f"/api/v1/activity-logs/?actor_user_id={authenticated_user.id}",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_activity_logs_search_by_event_type(self, authenticated_client, organization, authenticated_user):
        """Test searching activity logs by event type."""
        ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="task_created",
            target_type="Task",
            target_id=uuid.uuid4(),
        )
        ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="comment_added",
            target_type="Comment",
            target_id=uuid.uuid4(),
        )
        
        response = authenticated_client.get(
            "/api/v1/activity-logs/?search=task",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_activity_logs_ordering(self, authenticated_client, organization, authenticated_user):
        """Test ordering activity logs."""
        import time
        ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="first",
            target_type="Resource",
            target_id=uuid.uuid4(),
        )
        time.sleep(0.01)
        ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="second",
            target_type="Resource",
            target_id=uuid.uuid4(),
        )
        
        response = authenticated_client.get(
            "/api/v1/activity-logs/?ordering=-created_at",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["event_type"] == "second"

    @pytest.mark.permission
    def test_list_activity_logs_organization_isolation(self, authenticated_user, another_user):
        """Test that users only see logs from their organization."""
        from apps.organizations.models import Organization, OrganizationMembership, Role
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        org1 = Organization.objects.create(
            name="Org 1",
            slug="org-1",
            owner_user=authenticated_user,
        )
        org2 = Organization.objects.create(
            name="Org 2",
            slug="org-2",
            owner_user=another_user,
        )
        
        ActivityLog.objects.create(
            organization=org1,
            actor_user=authenticated_user,
            event_type="org1_event",
            target_type="Task",
            target_id=uuid.uuid4(),
        )
        ActivityLog.objects.create(
            organization=org2,
            actor_user=another_user,
            event_type="org2_event",
            target_type="Task",
            target_id=uuid.uuid4(),
        )
        
        client = APIClient()
        refresh = RefreshToken.for_user(authenticated_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        response = client.get(
            "/api/v1/activity-logs/",
            HTTP_X_ORGANIZATION_ID=str(org1.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["event_type"] == "org1_event"

