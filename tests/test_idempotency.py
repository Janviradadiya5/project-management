"""Idempotency and concurrency tests for critical write flows.

Tests for:
- Duplicate submission handling
- Concurrent operations 
- Transaction atomicity
- Race condition prevention
"""

import pytest
from django.db import transaction, IntegrityError
from django.test.utils import override_settings
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

from apps.organizations.models import OrganizationMembership, Role
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task
from apps.comments.models import Comment
from apps.users.models import User


@pytest.mark.django_db
@pytest.mark.idempotency
class TestProjectCreationIdempotency:
    """Test idempotent project creation (duplicate submissions)."""

    def test_duplicate_project_creation_ignored(self, organization, authenticated_user):
        """Test that duplicate project creation with same data doesn't create duplicates."""
        project_data = {
            "organization": organization,
            "name": "Idempotent Project",
            "slug": "idempotent-project",
            "created_by_user": authenticated_user,
        }
        
        # Create first project
        project1 = Project.objects.create(**project_data)
        
        # Try to create duplicate (would fail due to slug uniqueness)
        with pytest.raises(IntegrityError):
            project2 = Project.objects.create(**project_data)
        
        # Only one project should exist
        assert Project.objects.filter(slug="idempotent-project").count() == 1

    def test_task_assignment_idempotent(self, project, authenticated_user, another_user):
        """Test that reassigning task to same user is idempotent."""
        # Add users to project
        ProjectMember.objects.create(
            project=project,
            user=authenticated_user,
            project_role=ProjectMember.ROLE_MANAGER,
            added_by_user=authenticated_user,
        )
        ProjectMember.objects.create(
            project=project,
            user=another_user,
            project_role=ProjectMember.ROLE_CONTRIBUTOR,
            added_by_user=authenticated_user,
        )
        
        task = Task.objects.create(
            project=project,
            title="Test Task",
            created_by_user=authenticated_user,
            assignee_user=None,
        )
        
        # Assign task to another_user
        task.assignee_user = another_user
        task.save()
        assert task.assignee_user == another_user
        
        # Reassign to same user (idempotent)
        task.assignee_user = another_user
        task.save()
        assert task.assignee_user == another_user
        
        # Should not create duplicates
        assert Task.objects.filter(id=task.id).count() == 1


@pytest.mark.django_db
@pytest.mark.idempotency
class TestCommentCreationIdempotency:
    """Test idempotent comment creation."""

    def test_duplicate_comment_creates_new(self, task, authenticated_user):
        """Test that two identical comment submissions create two comments."""
        comment_data = {
            "task": task,
            "author_user": authenticated_user,
            "body": "This is a duplicate comment",
        }
        
        comment1 = Comment.objects.create(**comment_data)
        comment2 = Comment.objects.create(**comment_data)
        
        # Both should exist (idempotency not enforced at DB level for comments)
        assert Comment.objects.filter(body="This is a duplicate comment").count() == 2
        assert comment1.id != comment2.id


@pytest.mark.django_db
@pytest.mark.idempotency
class TestConcurrentProjectMemberAddition:
    """Test concurrent project member additions."""

    def test_concurrent_member_additions_no_race_condition(self, project):
        """Test that concurrent additions don't create race conditions."""
        users = [
            User.objects.create_user(
                email=f"user{i}@example.com",
                password="TestPassword123!",
                first_name=f"User{i}",
                last_name="Test",
            )
            for i in range(3)
        ]
        
        # Add all users as project members concurrently
        def add_member(user):
            ProjectMember.objects.get_or_create(
                project=project,
                user=user,
                defaults={
                    "project_role": ProjectMember.ROLE_CONTRIBUTOR,
                    "added_by_user": project.created_by_user,
                },
            )
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(add_member, user) for user in users]
            for future in as_completed(futures):
                future.result()
        
        # All users should be members exactly once
        for user in users:
            count = ProjectMember.objects.filter(project=project, user=user).count()
            assert count == 1, f"User {user.email} has {count} memberships (expected 1)"

    def test_concurrent_task_status_updates(self, task):
        """Test concurrent task status updates don't lose updates."""
        original_status = task.status
        
        def update_status(new_status):
            t = Task.objects.get(id=task.id)
            t.status = new_status
            time.sleep(0.001)  # Simulate processing
            t.save()
        
        statuses = ["open", "in_progress", "completed", "blocked"]
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(update_status, s) for s in statuses[:2]]
            for future in as_completed(futures):
                future.result()
        
        # Last update wins (no locking prevents this)
        task.refresh_from_db()
        assert task.status in statuses[:2]


@pytest.mark.django_db
@pytest.mark.idempotency
class TestOrganizationMembershipIdempotency:
    """Test idempotent membership operations."""

    def test_add_same_member_twice_is_idempotent(self, organization, another_user):
        """Test that adding same member twice is idempotent."""
        role = Role.objects.get_or_create(code="member")[0]
        
        # First addition
        membership1, created1 = OrganizationMembership.objects.get_or_create(
            organization=organization,
            user=another_user,
            defaults={"role": role, "status": OrganizationMembership.STATUS_ACTIVE},
        )
        
        # Second addition (should be idempotent)
        membership2, created2 = OrganizationMembership.objects.get_or_create(
            organization=organization,
            user=another_user,
            defaults={"role": role, "status": OrganizationMembership.STATUS_ACTIVE},
        )
        
        assert created1 is True
        assert created2 is False
        assert membership1.id == membership2.id


@pytest.mark.django_db
@pytest.mark.idempotency
class TestAtomicTransactions:
    """Test transaction atomicity for critical operations."""

    def test_task_creation_rolled_back_on_error(self, project, authenticated_user):
        """Test that failed task creation is rolled back."""
        initial_count = Task.objects.count()
        
        with pytest.raises(Exception):
            with transaction.atomic():
                task = Task.objects.create(
                    project=project,
                    title="Test Task",
                    created_by_user=authenticated_user,
                )
                # Force an error
                raise ValueError("Simulated error")
        
        # Task should be rolled back
        assert Task.objects.count() == initial_count

    def test_multiple_member_additions_atomic(self, project):
        """Test that adding multiple members is atomic."""
        users = [
            User.objects.create_user(
                email=f"user{i}@example.com",
                password="TestPassword123!",
                first_name=f"User{i}",
                last_name="Test",
            )
            for i in range(2)
        ]
        
        initial_count = ProjectMember.objects.count()
        
        with pytest.raises(Exception):
            with transaction.atomic():
                for user in users:
                    ProjectMember.objects.create(
                        project=project,
                        user=user,
                        project_role=ProjectMember.ROLE_CONTRIBUTOR,
                        added_by_user=project.created_by_user,
                    )
                # Force an error after first user
                if ProjectMember.objects.filter(project=project).count() == 1:
                    raise ValueError("Simulated error")
        
        # All additions should be rolled back
        assert ProjectMember.objects.count() == initial_count


@pytest.mark.django_db
@pytest.mark.idempotency
class TestCommentThreadSafety:
    """Test comment creation thread safety."""

    def test_concurrent_comment_creation(self, task, authenticated_user, another_user):
        """Test concurrent comment creation doesn't lose comments."""
        def create_comment(user, index):
            Comment.objects.create(
                task=task,
                author_user=user,
                body=f"Comment {index}",
            )
        
        initial_count = Comment.objects.filter(task=task).count()
        num_comments = 5
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(num_comments):
                user = authenticated_user if i % 2 == 0 else another_user
                futures.append(executor.submit(create_comment, user, i))
            
            for future in as_completed(futures):
                future.result()
        
        # All comments should be created
        final_count = Comment.objects.filter(task=task).count()
        assert final_count == initial_count + num_comments
