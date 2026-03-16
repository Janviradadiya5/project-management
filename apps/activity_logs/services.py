"""Service-layer business logic for app: activity_logs."""

from uuid import UUID

from apps.activity_logs.models import ActivityLog
from apps.organizations.models import OrganizationMembership
from apps.users.models import User


class ActivityLogService:
    @staticmethod
    def can_view_activity_logs(user: User, org_id) -> bool:
        """Check if user can view activity logs."""
        try:
            return OrganizationMembership.objects.filter(
                user=user,
                organization_id=org_id,
                role__code="organization_admin",
                status=OrganizationMembership.STATUS_ACTIVE,
            ).exists()
        except Exception:
            return False

    @staticmethod
    def log_activity(
        organization,
        actor_user: User,
        event_type: str,
        target_type: str,
        target_id: UUID,
        metadata: dict = None,
        request_id: UUID = None,
    ) -> ActivityLog:
        """Create activity log entry."""
        return ActivityLog.objects.create(
            organization=organization,
            actor_user=actor_user,
            event_type=event_type,
            target_type=target_type,
            target_id=target_id,
            metadata_json=metadata or {},
            request_id=request_id,
        )

