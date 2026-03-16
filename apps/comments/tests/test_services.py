"""Tests for Comment service business logic."""

import pytest

from apps.comments.services import CommentService
from apps.projects.models import ProjectMember


@pytest.mark.django_db
class TestCommentService:
    """Test cases for CommentService methods."""

    @pytest.mark.permission
    def test_can_access_task_as_project_member(self, task, authenticated_user):
        """Test that project members can access task."""
        assert ProjectMember.objects.filter(
            user=authenticated_user,
            project=task.project,
        ).exists()
        assert CommentService.can_access_task(authenticated_user, task) is True

    @pytest.mark.permission
    def test_cannot_access_task_not_member(self, task, another_user):
        """Test that non-members cannot access task."""
        assert CommentService.can_access_task(another_user, task) is False

    @pytest.mark.permission
    def test_can_access_task_with_any_role(self, task, authenticated_user, another_user):
        """Test that any project role can access task."""
        for role in [ProjectMember.ROLE_MANAGER, ProjectMember.ROLE_CONTRIBUTOR, ProjectMember.ROLE_VIEWER]:
            ProjectMember.objects.filter(
                user=another_user,
                project=task.project,
            ).delete()
            ProjectMember.objects.create(
                project=task.project,
                user=another_user,
                project_role=role,
                added_by_user=authenticated_user,
            )
            assert CommentService.can_access_task(another_user, task) is True

    def test_service_uses_real_queries(self, task, authenticated_user, another_user):
        """Test that service uses real database queries."""
        # Initially cannot access
        assert CommentService.can_access_task(another_user, task) is False
        
        # Add as member
        ProjectMember.objects.create(
            project=task.project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        
        # Now can access
        assert CommentService.can_access_task(another_user, task) is True

