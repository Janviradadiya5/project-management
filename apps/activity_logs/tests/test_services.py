"""Tests for ActivityLog service business logic."""

import pytest
import uuid

from apps.activity_logs.services import ActivityLogService
from apps.organizations.models import OrganizationMembership, Role


@pytest.mark.django_db
class TestActivityLogService:
    """Test cases for ActivityLogService methods."""

    @pytest.mark.permission
    def test_can_view_activity_logs_as_admin(self, organization, authenticated_user):
        """Test that organization admins can view activity logs."""
        admin_role = Role.objects.get_or_create(code="organization_admin")[0]
        OrganizationMembership.objects.create(
            organization=organization,
            user=authenticated_user,
            role=admin_role,
            status=OrganizationMembership.STATUS_ACTIVE,
        )
        assert ActivityLogService.can_view_activity_logs(authenticated_user, organization.id) is True

    @pytest.mark.permission
    def test_cannot_view_activity_logs_non_admin(self, organization, authenticated_user, another_user):
        """Test that non-admins cannot view activity logs."""
        org_role = Role.objects.get_or_create(code="organization_member")[0]
        OrganizationMembership.objects.create(
            organization=organization,
            user=another_user,
            role=org_role,
            status=OrganizationMembership.STATUS_ACTIVE,
        )
        assert ActivityLogService.can_view_activity_logs(another_user, organization.id) is False

    @pytest.mark.permission
    def test_cannot_view_activity_logs_not_member(self, organization, another_user):
        """Test that non-members cannot view activity logs."""
        assert ActivityLogService.can_view_activity_logs(another_user, organization.id) is False

    def test_log_activity_success(self, organization, authenticated_user):
        """Test successfully logging activity."""
        target_id = uuid.uuid4()
        req_id = uuid.uuid4()
        metadata = {"action": "create", "resource": "Task"}
        
        log = ActivityLogService.log_activity(
            organization=organization,
            actor_user=authenticated_user,
            event_type="task_created",
            target_type="Task",
            target_id=target_id,
            metadata=metadata,
            request_id=req_id,
        )
        
        assert log.id is not None
        assert log.organization == organization
        assert log.actor_user == authenticated_user
        assert log.event_type == "task_created"
        assert log.metadata_json == metadata
        assert log.request_id == req_id

    def test_log_activity_metadata_optional(self, organization, authenticated_user):
        """Test that metadata is optional."""
        log = ActivityLogService.log_activity(
            organization=organization,
            actor_user=authenticated_user,
            event_type="event",
            target_type="Resource",
            target_id=uuid.uuid4(),
        )
        assert log.metadata_json == {}

    def test_log_activity_request_id_optional(self, organization, authenticated_user):
        """Test that request_id is optional."""
        log = ActivityLogService.log_activity(
            organization=organization,
            actor_user=authenticated_user,
            event_type="event",
            target_type="Resource",
            target_id=uuid.uuid4(),
            request_id=None,
        )
        assert log.request_id is None

    def test_log_activity_persists(self, organization, authenticated_user):
        """Test that activity is persisted to database."""
        initial_count = organization.activity_logs.count()
        
        ActivityLogService.log_activity(
            organization=organization,
            actor_user=authenticated_user,
            event_type="test",
            target_type="Test",
            target_id=uuid.uuid4(),
        )
        
        assert organization.activity_logs.count() == initial_count + 1

    def test_log_multiple_activities(self, organization, authenticated_user):
        """Test logging multiple activities."""
        for i in range(5):
            ActivityLogService.log_activity(
                organization=organization,
                actor_user=authenticated_user,
                event_type=f"event{i}",
                target_type="Resource",
                target_id=uuid.uuid4(),
            )
        
        assert organization.activity_logs.count() == 5

