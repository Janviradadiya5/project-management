"""Factory Boy factories for all models."""

import uuid
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.organizations.models import Organization, OrganizationMembership, Role
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task
from apps.comments.models import Comment
from apps.attachments.models import Attachment
from apps.notifications.models import Notification
from apps.activity_logs.models import ActivityLog

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_email_verified = True
    password = factory.PostGenerationMethodCall("set_password", "TestPassword123!")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override create to use create_user instead of create."""
        manager = cls._get_manager(model_class)
        password = kwargs.pop("password", None)
        obj = manager.create_user(*args, **kwargs)
        if password:
            obj.set_password(password)
            obj.save()
        return obj


class RoleFactory(DjangoModelFactory):
    """Factory for creating Role instances."""

    class Meta:
        model = Role

    code = factory.Sequence(lambda n: f"role_{n}")
    name = factory.Faker("word")
    description = factory.Faker("sentence")


class OrganizationFactory(DjangoModelFactory):
    """Factory for creating Organization instances."""

    class Meta:
        model = Organization

    name = factory.Faker("company")
    slug = factory.Slug()
    description = factory.Faker("sentence")
    owner_user = factory.SubFactory(UserFactory)
    status = "active"


class OrganizationMembershipFactory(DjangoModelFactory):
    """Factory for creating OrganizationMembership instances."""

    class Meta:
        model = OrganizationMembership

    organization = factory.SubFactory(OrganizationFactory)
    user = factory.SubFactory(UserFactory)
    role = factory.SubFactory(
        RoleFactory, code="organization_member", name="Organization Member"
    )
    status = OrganizationMembership.STATUS_ACTIVE


class ProjectFactory(DjangoModelFactory):
    """Factory for creating Project instances."""

    class Meta:
        model = Project

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Faker("sentence", nb_words=3)
    slug = factory.Slug()
    description = factory.Faker("sentence")
    status = "active"
    created_by_user = factory.SubFactory(UserFactory)
    deadline_at = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=30)
    )


class ProjectMemberFactory(DjangoModelFactory):
    """Factory for creating ProjectMember instances."""

    class Meta:
        model = ProjectMember

    project = factory.SubFactory(ProjectFactory)
    user = factory.SubFactory(UserFactory)
    project_role = ProjectMember.ROLE_CONTRIBUTOR
    added_by_user = factory.SubFactory(UserFactory)


class TaskFactory(DjangoModelFactory):
    """Factory for creating Task instances."""

    class Meta:
        model = Task

    project = factory.SubFactory(ProjectFactory)
    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("sentence")
    status = "open"
    priority = "medium"
    created_by_user = factory.SubFactory(UserFactory)
    assignee_user = factory.SubFactory(UserFactory)
    due_at = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=7)
    )
    completed_at = None


class CommentFactory(DjangoModelFactory):
    """Factory for creating Comment instances."""

    class Meta:
        model = Comment

    task = factory.SubFactory(TaskFactory)
    author_user = factory.SubFactory(UserFactory)
    body = factory.Faker("sentence")
    parent_comment = None
    is_edited = False


class AttachmentFactory(DjangoModelFactory):
    """Factory for creating Attachment instances."""

    class Meta:
        model = Attachment

    task = factory.SubFactory(TaskFactory)
    uploaded_by_user = factory.SubFactory(UserFactory)
    file_name = factory.LazyFunction(lambda: f"test_{uuid.uuid4()}.pdf")
    content_type = "application/pdf"
    size_bytes = 1024
    storage_key = factory.LazyFunction(
        lambda: f"s3://bucket/test_{uuid.uuid4()}.pdf"
    )
    checksum = factory.Faker("sha256")


class NotificationFactory(DjangoModelFactory):
    """Factory for creating Notification instances."""

    class Meta:
        model = Notification

    recipient_user = factory.SubFactory(UserFactory)
    event_type = "task_assigned"
    message = factory.Faker("sentence")
    link = None


class ActivityLogFactory(DjangoModelFactory):
    """Factory for creating ActivityLog instances."""

    class Meta:
        model = ActivityLog

    organization = factory.SubFactory(OrganizationFactory)
    user = factory.SubFactory(UserFactory)
    event_type = "organization_created"
    description = factory.Faker("sentence")
    metadata = {}
