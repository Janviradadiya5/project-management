"""Tests for Comment model."""

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.comments.models import Comment


@pytest.mark.django_db
class TestCommentModel:
    """Test cases for Comment model."""

    def test_create_comment_with_valid_data(self, task, authenticated_user):
        """Test creating a comment with valid data."""
        comment = Comment.objects.create(
            task=task,
            author_user=authenticated_user,
            body="Test comment",
        )
        assert comment.id is not None
        assert comment.task == task
        assert comment.author_user == authenticated_user
        assert comment.body == "Test comment"
        assert comment.is_edited is False
        assert comment.parent_comment is None
        assert comment.created_at is not None
        assert comment.updated_at is not None
        assert comment.deleted_at is None

    def test_comment_string_representation(self, comment):
        """Test __str__ method."""
        str_repr = str(comment)
        assert "Comment" in str_repr
        assert comment.task_id in str_repr

    def test_comment_timestamps_auto_generated(self, task, authenticated_user):
        """Test that created_at and updated_at are automatically set."""
        before = timezone.now()
        comment = Comment.objects.create(
            task=task,
            author_user=authenticated_user,
            body="Timestamp test",
        )
        after = timezone.now()
        assert before <= comment.created_at <= after
        assert before <= comment.updated_at <= after

    def test_comment_soft_delete(self, comment):
        """Test soft delete with deleted_at."""
        assert comment.deleted_at is None
        delete_time = timezone.now()
        comment.deleted_at = delete_time
        comment.save()
        comment.refresh_from_db()
        assert comment.deleted_at == delete_time

    def test_create_comment_reply(self, comment):
        """Test creating a reply to a comment."""
        reply = Comment.objects.create(
            task=comment.task,
            author_user=comment.author_user,
            body="Reply to comment",
            parent_comment=comment,
        )
        assert reply.parent_comment == comment
        assert comment.replies.count() == 1
        assert comment.replies.first() == reply

    def test_comment_parent_optional(self, task, authenticated_user):
        """Test that parent_comment is optional."""
        comment = Comment.objects.create(
            task=task,
            author_user=authenticated_user,
            body="Root comment",
            parent_comment=None,
        )
        assert comment.parent_comment is None

    def test_comment_foreign_key_task_cascade(self, comment):
        """Test that deleting task cascades to comments."""
        comment_id = comment.id
        task = comment.task
        task.delete()
        assert not Comment.objects.filter(id=comment_id).exists()

    def test_comment_parent_cascade(self, comment):
        """Test that deleting parent comment cascades to replies."""
        reply = Comment.objects.create(
            task=comment.task,
            author_user=comment.author_user,
            body="Reply",
            parent_comment=comment,
        )
        reply_id = reply.id
        comment.delete()
        assert not Comment.objects.filter(id=reply_id).exists()

    def test_comment_author_user_restrict(self, comment):
        """Test that deleting author is restricted."""
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            comment.author_user.delete()

    def test_comment_edited_flag(self, comment):
        """Test editing a comment sets is_edited."""
        assert comment.is_edited is False
        comment.body = "Updated body"
        comment.is_edited = True
        comment.save()
        comment.refresh_from_db()
        assert comment.is_edited is True

    def test_comment_updated_at_changes_on_update(self, comment):
        """Test that updated_at changes when comment is updated."""
        original_updated_at = comment.updated_at
        from time import sleep
        sleep(0.01)
        comment.body = "Modified"
        comment.save()
        comment.refresh_from_db()
        assert comment.updated_at > original_updated_at

    def test_multiple_replies_to_comment(self, comment, authenticated_user):
        """Test multiple replies to same comment."""
        reply1 = Comment.objects.create(
            task=comment.task,
            author_user=authenticated_user,
            body="Reply 1",
            parent_comment=comment,
        )
        reply2 = Comment.objects.create(
            task=comment.task,
            author_user=authenticated_user,
            body="Reply 2",
            parent_comment=comment,
        )
        assert comment.replies.count() == 2
        assert reply1 in comment.replies.all()
        assert reply2 in comment.replies.all()

    def test_nested_replies(self, comment, authenticated_user):
        """Test nested comment replies."""
        reply1 = Comment.objects.create(
            task=comment.task,
            author_user=authenticated_user,
            body="Reply 1",
            parent_comment=comment,
        )
        reply2 = Comment.objects.create(
            task=comment.task,
            author_user=authenticated_user,
            body="Reply to reply",
            parent_comment=reply1,
        )
        assert reply2.parent_comment == reply1
        assert reply1.replies.count() == 1

