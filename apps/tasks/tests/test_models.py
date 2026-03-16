"""Tests for Task model."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.tasks.models import Task
from apps.projects.models import Project, ProjectMember


@pytest.mark.django_db
class TestTaskModel:
    """Test cases for Task model."""

    def test_create_task_with_valid_data(self, project, authenticated_user):
        """Test creating a task with valid data."""
        task = Task.objects.create(
            project=project,
            title="Test Task",
            description="A test task",
            priority=Task.PRIORITY_MEDIUM,
            status=Task.STATUS_TODO,
            created_by_user=authenticated_user,
        )
        assert task.id is not None
        assert task.title == "Test Task"
        assert task.priority == Task.PRIORITY_MEDIUM
        assert task.status == Task.STATUS_TODO
        assert task.project == project
        assert task.created_by_user == authenticated_user
        assert task.created_at is not None
        assert task.updated_at is not None
        assert task.deleted_at is None

    def test_task_string_representation(self, task):
        """Test __str__ method returns task title."""
        assert str(task) == "Test Task"

    def test_create_task_with_all_fields(self, project, authenticated_user, another_user):
        """Test creating a task with all fields."""
        due_date = timezone.now() + timezone.timedelta(days=7)
        task = Task.objects.create(
            project=project,
            title="Complete Task",
            description="Full task",
            priority=Task.PRIORITY_HIGH,
            status=Task.STATUS_IN_PROGRESS,
            due_at=due_date,
            assignee_user=another_user,
            created_by_user=authenticated_user,
        )
        assert task.due_at == due_date
        assert task.assignee_user == another_user

    def test_task_timestamps_auto_generated(self, project, authenticated_user):
        """Test that created_at and updated_at are automatically set."""
        before = timezone.now()
        task = Task.objects.create(
            project=project,
            title="Timestamp Task",
            created_by_user=authenticated_user,
        )
        after = timezone.now()
        assert before <= task.created_at <= after
        assert before <= task.updated_at <= after

    def test_task_soft_delete_with_deleted_at(self, task):
        """Test soft delete functionality."""
        assert task.deleted_at is None
        delete_time = timezone.now()
        task.deleted_at = delete_time
        task.save()
        task.refresh_from_db()
        assert task.deleted_at == delete_time

    def test_task_priority_choices(self, project, authenticated_user):
        """Test that task priority must be valid choice."""
        for priority in [Task.PRIORITY_LOW, Task.PRIORITY_MEDIUM, Task.PRIORITY_HIGH]:
            task = Task.objects.create(
                project=project,
                title=f"Task {priority}",
                priority=priority,
                created_by_user=authenticated_user,
            )
            assert task.priority == priority

    def test_task_status_choices(self, project, authenticated_user):
        """Test that task status must be valid choice."""
        for status in [Task.STATUS_TODO, Task.STATUS_IN_PROGRESS, Task.STATUS_DONE]:
            task = Task.objects.create(
                project=project,
                title=f"Task {status}",
                status=status,
                created_by_user=authenticated_user,
            )
            assert task.status == status

    def test_task_clean_status_done_requires_completed_at(self, project, authenticated_user):
        """Test that status=done requires completed_at to be set."""
        task = Task(
            project=project,
            title="Done without completion",
            status=Task.STATUS_DONE,
            created_by_user=authenticated_user,
        )
        with pytest.raises(ValidationError):
            task.clean()

    def test_task_clean_completed_at_requires_done_status(self, project, authenticated_user):
        """Test that completed_at requires status=done."""
        task = Task(
            project=project,
            title="Completed but not done",
            status=Task.STATUS_TODO,
            completed_at=timezone.now(),
            created_by_user=authenticated_user,
        )
        with pytest.raises(ValidationError):
            task.clean()

    def test_task_clean_past_due_date_not_allowed_for_incomplete(self, project, authenticated_user):
        """Test that past due dates not allowed for incomplete tasks."""
        task = Task(
            project=project,
            title="Past due",
            status=Task.STATUS_TODO,
            due_at=timezone.now() - timezone.timedelta(days=1),
            created_by_user=authenticated_user,
        )
        with pytest.raises(ValidationError):
            task.clean()

    def test_task_clean_past_due_date_allowed_for_completed(self, project, authenticated_user):
        """Test that past due dates are allowed for completed tasks."""
        task = Task(
            project=project,
            title="Completed past due",
            status=Task.STATUS_DONE,
            due_at=timezone.now() - timezone.timedelta(days=1),
            completed_at=timezone.now(),
            created_by_user=authenticated_user,
        )
        task.clean()  # Should not raise
        task.save()
        assert task.id is not None

    def test_task_clean_assignee_must_be_project_member(self, project, authenticated_user, another_user):
        """Test that assignee must be a project member."""
        task = Task(
            project=project,
            title="Invalid assignee",
            assignee_user=another_user,
            created_by_user=authenticated_user,
        )
        with pytest.raises(ValidationError):
            task.clean()

    def test_task_clean_valid_member_as_assignee(self, project, authenticated_user, another_user):
        """Test that project member can be assigned."""
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        task = Task(
            project=project,
            title="Valid assignee",
            assignee_user=another_user,
            created_by_user=authenticated_user,
        )
        task.clean()
        task.save()
        assert task.assignee_user == another_user

    def test_task_assignee_can_be_null(self, project, authenticated_user):
        """Test that assignee_user is optional."""
        task = Task.objects.create(
            project=project,
            title="Unassigned",
            assignee_user=None,
            created_by_user=authenticated_user,
        )
        assert task.assignee_user is None

    def test_task_foreign_key_project_cascade(self, task):
        """Test that deleting project cascades to tasks."""
        task_id = task.id
        project = task.project
        project.delete()
        assert not Task.objects.filter(id=task_id).exists()

    def test_task_assignee_null_on_user_delete(self, project, authenticated_user, another_user):
        """Test that assignee is nulled when user is deleted."""
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        task = Task.objects.create(
            project=project,
            title="Will lose assignee",
            assignee_user=another_user,
            created_by_user=authenticated_user,
        )
        task_id = task.id
        another_user.delete()
        task.refresh_from_db()
        assert task.assignee_user is None

    def test_task_created_by_restrict_on_delete(self, project, task, authenticated_user):
        """Test that deleting creator is restricted."""
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            authenticated_user.delete()

    def test_task_default_priority(self, project, authenticated_user):
        """Test that default priority is medium."""
        task = Task.objects.create(
            project=project,
            title="Default priority",
            created_by_user=authenticated_user,
        )
        assert task.priority == Task.PRIORITY_MEDIUM

    def test_task_default_status(self, project, authenticated_user):
        """Test that default status is todo."""
        task = Task.objects.create(
            project=project,
            title="Default status",
            created_by_user=authenticated_user,
        )
        assert task.status == Task.STATUS_TODO

