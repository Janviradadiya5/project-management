"""Tests for Notification REST API endpoints."""

import pytest
from rest_framework import status
from django.utils import timezone

from apps.notifications.models import Notification


@pytest.mark.django_db
class TestNotificationListApi:
    """Test cases for Notification list endpoint."""

    @pytest.mark.auth
    def test_list_notifications_authentication_required(self, api_client):
        """Test that authentication is required."""
        response = api_client.get("/api/v1/notifications/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_notifications_success(self, authenticated_client, organization, authenticated_user):
        """Test successfully listing notifications."""
        Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="type1",
            title="Notification 1",
            body="Body 1",
        )
        Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="type2",
            title="Notification 2",
            body="Body 2",
        )
        
        response = authenticated_client.get("/api/v1/notifications/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_list_notifications_pagination(self, authenticated_client, organization, authenticated_user):
        """Test notification list pagination."""
        for i in range(15):
            Notification.objects.create(
                recipient_user=authenticated_user,
                organization=organization,
                type=f"type{i}",
                title=f"Notification {i}",
                body=f"Body {i}",
            )
        
        response = authenticated_client.get("/api/v1/notifications/?page=1")
        assert response.status_code == status.HTTP_200_OK
        assert "next" in response.data

    def test_list_notifications_filter_by_is_read(self, authenticated_client, organization, authenticated_user):
        """Test filtering notifications by read status."""
        Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="unread",
            title="Unread",
            body="This is unread",
            is_read=False,
        )
        Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="read",
            title="Read",
            body="This is read",
            is_read=True,
            read_at=timezone.now(),
        )
        
        response = authenticated_client.get("/api/v1/notifications/?is_read=false")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["is_read"] is False

    def test_list_notifications_filter_by_type(self, authenticated_client, organization, authenticated_user):
        """Test filtering notifications by type."""
        Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="task_assigned",
            title="Task",
            body="Task body",
        )
        Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="comment_added",
            title="Comment",
            body="Comment body",
        )
        
        response = authenticated_client.get("/api/v1/notifications/?type=task_assigned")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_notifications_ordering(self, authenticated_client, organization, authenticated_user):
        """Test notification list ordering."""
        import time
        Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="first",
            title="First",
            body="First",
        )
        time.sleep(0.01)
        Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="second",
            title="Second",
            body="Second",
        )
        
        response = authenticated_client.get("/api/v1/notifications/?ordering=-created_at")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["type"] == "second"

    @pytest.mark.permission
    def test_list_notifications_only_own(self, authenticated_user, another_user, organization):
        """Test that users only see their own notifications."""
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="user1",
            title="User 1",
            body="User 1 notification",
        )
        Notification.objects.create(
            recipient_user=another_user,
            organization=organization,
            type="user2",
            title="User 2",
            body="User 2 notification",
        )
        
        client = APIClient()
        refresh = RefreshToken.for_user(another_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        response = client.get("/api/v1/notifications/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["type"] == "user2"


@pytest.mark.django_db
class TestNotificationMarkAsReadApi:
    """Test cases for mark as read endpoint."""

    def test_mark_as_read_success(self, authenticated_client, notification, authenticated_user):
        """Test successfully marking notification as read."""
        assert notification.is_read is False
        
        response = authenticated_client.patch(
            f"/api/v1/notifications/{notification.id}/mark-as-read/",
        )
        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.is_read is True
        assert notification.read_at is not None

    @pytest.mark.negative
    def test_mark_as_read_not_found(self, authenticated_client):
        """Test marking non-existent notification as read."""
        import uuid
        response = authenticated_client.patch(
            f"/api/v1/notifications/{uuid.uuid4()}/mark-as-read/",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.permission
    def test_mark_as_read_not_own(self, authenticated_user, another_user, organization):
        """Test that users cannot mark others' notifications as read."""
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        notification = Notification.objects.create(
            recipient_user=authenticated_user,
            organization=organization,
            type="test",
            title="Test",
            body="Test",
        )
        
        client = APIClient()
        refresh = RefreshToken.for_user(another_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        response = client.patch(
            f"/api/v1/notifications/{notification.id}/mark-as-read/",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.auth
    def test_mark_as_read_requires_auth(self, api_client, notification):
        """Test that authentication is required."""
        response = api_client.patch(
            f"/api/v1/notifications/{notification.id}/mark-as-read/",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

