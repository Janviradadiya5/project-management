"""Tests for ActivityLog model."""

import pytest
import uuid
from django.utils import timezone

from apps.activity_logs.models import ActivityLog


@pytest.mark.django_db
class TestActivityLogModel:
    """Test cases for ActivityLog model."""

    def test_create_activity_log_with_valid_data(self, organization, authenticated_user):
        """Test creating an activity log with valid data."""
        target_id = uuid.uuid4()
        req_id = uuid.uuid4()
        
        log = ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="task_created",
            target_type="Task",
            target_id=target_id,
            metadata_json={"title": "New Task"},
            request_id=req_id,
        )
        
        assert log.id is not None
        assert log.organization == organization
        assert log.actor_user == authenticated_user
        assert log.event_type == "task_created"
        assert log.target_type == "Task"
        assert log.target_id == target_id
        assert log.metadata_json == {"title": "New Task"}
        assert log.request_id == req_id
        assert log.created_at is not None

    def test_activity_log_string_representation(self, organization, authenticated_user):
        """Test __str__ method."""
        log = ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="project_updated",
            target_type="Project",
            target_id=uuid.uuid4(),
        )
        str_repr = str(log)
        assert "ActivityLog" in str_repr
        assert "project_updated" in str_repr

    def test_activity_log_created_at_auto_generated(self, organization, authenticated_user):
        """Test that created_at is automatically set."""
        before = timezone.now()
        log = ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="event",
            target_type="Target",
            target_id=uuid.uuid4(),
        )
        after = timezone.now()
        assert before <= log.created_at <= after

    def test_activity_log_with_complex_metadata(self, organization, authenticated_user):
        """Test creating log with complex metadata."""
        metadata = {
            "old_status": "active",
            "new_status": "archived",
            "changed_at": "2024-03-13T10:30:00Z",
            "changed_by": str(authenticated_user.id),
            "reason": "Project completed",
            "tags": ["migration", "archive"],
            "nested": {"level1": {"level2": "value"}},
        }
        log = ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="project_archived",
            target_type="Project",
            target_id=uuid.uuid4(),
            metadata_json=metadata,
        )
        log.refresh_from_db()
        assert log.metadata_json == metadata
        assert log.metadata_json["nested"]["level2"] == "value"

    def test_activity_log_metadata_optional(self, organization, authenticated_user):
        """Test that metadata is optional."""
        log = ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="simple_event",
            target_type="Resource",
            target_id=uuid.uuid4(),
        )
        assert log.metadata_json == {}

    def test_activity_log_request_id_optional(self, organization, authenticated_user):
        """Test that request_id is optional."""
        log = ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="event",
            target_type="Target",
            target_id=uuid.uuid4(),
            request_id=None,
        )
        assert log.request_id is None

    def test_activity_log_foreign_key_org_restrict(self, organization, authenticated_user):
        """Test that deleting organization is restricted."""
        ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="test",
            target_type="Test",
            target_id=uuid.uuid4(),
        )
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            organization.delete()

    def test_activity_log_foreign_key_user_restrict(self, organization, authenticated_user):
        """Test that deleting actor is restricted."""
        ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="test",
            target_type="Test",
            target_id=uuid.uuid4(),
        )
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            authenticated_user.delete()

    def test_activity_log_various_event_types(self, organization, authenticated_user):
        """Test various event types."""
        event_types = [
            "task_created",
            "task_updated",
            "task_deleted",
            "comment_added",
            "attachment_uploaded",
            "project_archived",
            "user_invited",
            "permission_changed",
        ]
        for event_type in event_types:
            log = ActivityLog.objects.create(
                organization=organization,
                actor_user=authenticated_user,
                event_type=event_type,
                target_type="Resource",
                target_id=uuid.uuid4(),
            )
            assert log.event_type == event_type

    def test_activity_log_various_target_types(self, organization, authenticated_user):
        """Test various target types."""
        target_types = [
            "Task",
            "Project",
            "Comment",
            "Attachment",
            "User",
            "Organization",
        ]
        for target_type in target_types:
            log = ActivityLog.objects.create(
                organization=organization,
                actor_user=authenticated_user,
                event_type="event",
                target_type=target_type,
                target_id=uuid.uuid4(),
            )
            assert log.target_type == target_type

    def test_activity_log_append_only_design(self, organization, authenticated_user):
        """Test that activity logs are created, not updated."""
        log = ActivityLog.objects.create(
            organization=organization,
            actor_user=authenticated_user,
            event_type="created",
            target_type="Task",
            target_id=uuid.uuid4(),
        )
        original_created = log.created_at
        
        # Note: The design is append-only, so we shouldn't update
        # But test that we can read what was created
        log.refresh_from_db()
        assert log.created_at == original_created

