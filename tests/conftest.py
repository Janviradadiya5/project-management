# Shared pytest fixtures go here.

import uuid
import jwt
from datetime import datetime, timedelta
from django.utils import timezone
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.organizations.models import Organization, OrganizationMembership, Role
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task
from apps.comments.models import Comment
from apps.attachments.models import Attachment
from apps.notifications.models import Notification
from apps.activity_logs.models import ActivityLog

User = get_user_model()


@pytest.fixture
def api_client():
    """API client for testing REST endpoints."""
    return APIClient()


@pytest.fixture
def authenticated_user(db):
    """Create and return an authenticated test user."""
    user = User.objects.create_user(
        email="testuser@example.com",
        password="TestPassword123!",
        first_name="Test",
        last_name="User",
        is_email_verified=True,
    )
    return user


@pytest.fixture
def another_user(db):
    """Create and return a second test user."""
    user = User.objects.create_user(
        email="another@example.com",
        password="TestPassword123!",
        first_name="Another",
        last_name="User",
        is_email_verified=True,
    )
    return user


@pytest.fixture
def unverified_user(db):
    """Create a user with unverified email."""
    user = User.objects.create_user(
        email="unverified@example.com",
        password="TestPassword123!",
        first_name="Unverified",
        last_name="User",
        is_email_verified=False,
    )
    return user


@pytest.fixture
def jwt_token(authenticated_user):
    """Generate JWT token for authenticated user."""
    refresh = RefreshToken.for_user(authenticated_user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


@pytest.fixture
def authenticated_client(api_client, jwt_token):
    """API client with JWT authentication."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_token['access']}")
    return api_client


@pytest.fixture
def organization(db, authenticated_user):
    """Create a test organization."""
    org = Organization.objects.create(
        name="Test Org",
        slug="test-org",
        description="Test organization for unit tests",
        owner_user=authenticated_user,
        status="active",
    )
    # Add authenticated user as admin member
    admin_role = Role.objects.get_or_create(code="organization_admin")[0]
    OrganizationMembership.objects.create(
        organization=org,
        user=authenticated_user,
        role=admin_role,
        status=OrganizationMembership.STATUS_ACTIVE,
    )
    return org


@pytest.fixture
def org_member_role(db):
    """Get or create organization member role."""
    role, _ = Role.objects.get_or_create(
        code="organization_member",
        defaults={"name": "Organization Member"},
    )
    return role


@pytest.fixture
def member_in_org(db, organization, another_user, org_member_role):
    """Add another_user as member in organization."""
    OrganizationMembership.objects.create(
        organization=organization,
        user=another_user,
        role=org_member_role,
        status=OrganizationMembership.STATUS_ACTIVE,
    )
    return another_user


@pytest.fixture
def project(db, organization, authenticated_user):
    """Create a test project."""
    project = Project.objects.create(
        organization=organization,
        name="Test Project",
        slug="test-project",
        description="Test project for unit tests",
        status="active",
        created_by_user=authenticated_user,
    )
    # Add authenticated user as project manager
    ProjectMember.objects.create(
        project=project,
        user=authenticated_user,
        project_role=ProjectMember.ROLE_MANAGER,
        added_by_user=authenticated_user,
    )
    return project


@pytest.fixture
def project_contributor(db, project, another_user):
    """Add another_user as contributor to project."""
    ProjectMember.objects.create(
        project=project,
        user=another_user,
        project_role=ProjectMember.ROLE_CONTRIBUTOR,
        added_by_user=project.created_by_user,
    )
    return another_user


@pytest.fixture
def task(db, project, authenticated_user):
    """Create a test task."""
    task = Task.objects.create(
        project=project,
        title="Test Task",
        description="Test task for unit tests",
        status="open",
        priority="medium",
        created_by_user=authenticated_user,
        assignee_user=authenticated_user,
        due_at=timezone.now() + timedelta(days=7),
    )
    return task


@pytest.fixture
def comment(db, task, authenticated_user):
    """Create a test comment (not a reply)."""
    comment = Comment.objects.create(
        task=task,
        author_user=authenticated_user,
        body="Test comment",
    )
    return comment


@pytest.fixture
def attachment(db, task, authenticated_user):
    """Create a test attachment."""
    attachment = Attachment.objects.create(
        task=task,
        uploaded_by_user=authenticated_user,
        file_name="test.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        storage_key="s3://bucket/test.pdf",
        checksum="abc123def456",
    )
    return attachment


@pytest.fixture
def notification(db, authenticated_user):
    """Create a test notification."""
    notification = Notification.objects.create(
        recipient_user=authenticated_user,
        event_type="task_assigned",
        message="You have been assigned to a task",
    )
    return notification


@pytest.fixture
def activity_log(db, organization, authenticated_user):
    """Create a test activity log."""
    log = ActivityLog.objects.create(
        organization=organization,
        user=authenticated_user,
        event_type="project_created",
        description="Test project was created",
    )
    return log


@pytest.fixture
def client_with_org_header(authenticated_client, organization):
    """Authenticated client with X-Organization-ID header."""
    authenticated_client.defaults["HTTP_X_ORGANIZATION_ID"] = str(organization.id)
    return authenticated_client


# Database markers
pytestmark = pytest.mark.django_db


@pytest.fixture
def transactional_db(db):
    """Mark test as requiring transactional DB access."""
    return db


