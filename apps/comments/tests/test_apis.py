"""Tests for Comment REST API endpoints."""

import pytest
from rest_framework import status

from apps.comments.models import Comment
from apps.projects.models import ProjectMember


@pytest.mark.django_db
class TestCommentListApi:
    """Test cases for task comments list endpoint."""

    @pytest.mark.auth
    def test_list_comments_authentication_required(self, api_client, task):
        """Test that authentication is required."""
        response = api_client.get(
            f"/api/v1/tasks/{task.id}/comments/",
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_comments_success(self, authenticated_client, task, authenticated_user):
        """Test successfully listing comments."""
        Comment.objects.create(
            task=task,
            author_user=authenticated_user,
            body="Comment 1",
        )
        Comment.objects.create(
            task=task,
            author_user=authenticated_user,
            body="Comment 2",
        )
        
        response = authenticated_client.get(
            f"/api/v1/tasks/{task.id}/comments/",
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    @pytest.mark.permission
    def test_list_comments_permission_denied_non_member(self, task, another_user):
        """Test that non-members cannot list comments."""
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        client = APIClient()
        refresh = RefreshToken.for_user(another_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        response = client.get(
            f"/api/v1/tasks/{task.id}/comments/",
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_comment_success(self, authenticated_client, task):
        """Test successfully creating a comment."""
        response = authenticated_client.post(
            f"/api/v1/tasks/{task.id}/comments/",
            {
                "body": "New comment",
            },
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["body"] == "New comment"
        assert response.data["success"] is True

    @pytest.mark.negative
    def test_create_comment_empty_body(self, authenticated_client, task):
        """Test that empty comment body is rejected."""
        response = authenticated_client.post(
            f"/api/v1/tasks/{task.id}/comments/",
            {
                "body": "",
            },
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.negative
    def test_create_comment_xss_detection(self, authenticated_client, task):
        """Test that XSS attempts are rejected."""
        response = authenticated_client.post(
            f"/api/v1/tasks/{task.id}/comments/",
            {
                "body": "<script>alert('xss')</script>",
            },
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_comment_with_parent(self, authenticated_client, comment, task):
        """Test creating a reply to a comment."""
        response = authenticated_client.post(
            f"/api/v1/tasks/{task.id}/comments/",
            {
                "body": "Reply to comment",
                "parent_comment_id": str(comment.id),
            },
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["parent_comment_id"] == str(comment.id)

    def test_create_comment_sets_author(self, authenticated_client, task, authenticated_user):
        """Test that author is set to current user."""
        response = authenticated_client.post(
            f"/api/v1/tasks/{task.id}/comments/",
            {
                "body": "Author test",
            },
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        comment = Comment.objects.get(id=response.data["data"]["id"])
        assert comment.author_user == authenticated_user


@pytest.mark.django_db
class TestCommentUpdateApi:
    """Test cases for Comment update endpoint."""

    def test_update_comment_success(self, authenticated_client, comment):
        """Test successfully updating a comment."""
        response = authenticated_client.patch(
            f"/api/v1/comments/{comment.id}/",
            {
                "body": "Updated comment",
            },
            HTTP_X_ORGANIZATION_ID=str(comment.task.project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        comment.refresh_from_db()
        assert comment.body == "Updated comment"
        assert comment.is_edited is True

    @pytest.mark.permission
    def test_update_comment_not_author(self, authenticated_user, another_user):
        """Test that non-authors cannot update comments."""
        from apps.comments.models import Comment
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        comment = Comment.objects.create(
            task=self.task,
            author_user=authenticated_user,
            body="Original",
        )
        
        client = APIClient()
        refresh = RefreshToken.for_user(another_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        response = client.patch(
            f"/api/v1/comments/{comment.id}/",
            {"body": "Hacked"},
            HTTP_X_ORGANIZATION_ID=str(comment.task.project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.negative
    def test_update_comment_not_found(self, authenticated_client, task):
        """Test updating non-existent comment."""
        import uuid
        response = authenticated_client.patch(
            f"/api/v1/comments/{uuid.uuid4()}/",
            {"body": "Should fail"},
            HTTP_X_ORGANIZATION_ID=str(task.project.organization.id),
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCommentDeleteApi:
    """Test cases for Comment delete endpoint."""

    def test_delete_comment_success(self, authenticated_client, comment):
        """Test successfully deleting a comment."""
        comment_id = comment.id
        response = authenticated_client.delete(
            f"/api/v1/comments/{comment_id}/",
            HTTP_X_ORGANIZATION_ID=str(comment.task.project.organization.id),
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]
        assert not Comment.objects.filter(id=comment_id).exists()

    @pytest.mark.permission
    def test_delete_comment_not_author(self, authenticated_user, another_user):
        """Test that non-authors cannot delete comments."""
        from apps.comments.models import Comment
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        from apps.projects.models import Project
        from apps.tasks.models import Task
        from apps.organizations.models import Organization
        
        org = Organization.objects.create(
            name="Test Org",
            slug="test-org",
            owner_user=authenticated_user,
        )
        project = Project.objects.create(
            organization=org,
            name="Test Project",
            created_by_user=authenticated_user,
        )
        task = Task.objects.create(
            project=project,
            title="Test Task",
            created_by_user=authenticated_user,
        )
        comment = Comment.objects.create(
            task=task,
            author_user=authenticated_user,
            body="Original",
        )
        
        client = APIClient()
        refresh = RefreshToken.for_user(another_user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        
        response = client.delete(
            f"/api/v1/comments/{comment.id}/",
            HTTP_X_ORGANIZATION_ID=str(org.id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.auth
    def test_delete_comment_requires_auth(self, api_client, comment):
        """Test that authentication is required."""
        response = api_client.delete(
            f"/api/v1/comments/{comment.id}/",
            HTTP_X_ORGANIZATION_ID=str(comment.task.project.organization.id),
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

