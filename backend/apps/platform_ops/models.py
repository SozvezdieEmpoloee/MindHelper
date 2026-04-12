import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class NeuralModelVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version_tag = models.CharField(max_length=64, unique=True)
    model_name = models.CharField(max_length=120)
    provider = models.CharField(max_length=120)
    safety_profile = models.CharField(max_length=64)
    is_active = models.BooleanField(default=False)
    deployed_at = models.DateTimeField(blank=True, null=True)
    created_by_admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name="created_model_versions",
    )

    class Meta:
        db_table = "neural_model_version"
        ordering = ("-deployed_at", "version_tag")

    def __str__(self) -> str:
        return self.version_tag


class ModerationCase(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_REVIEW = "in_review", "In review"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(
        "chat.UserChat",
        on_delete=models.CASCADE,
        related_name="moderation_cases",
    )
    message = models.ForeignKey(
        "chat.ChatMessage",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="moderation_cases",
    )
    reason = models.TextField()
    status = models.CharField(max_length=32, choices=Status.choices)
    opened_by_admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name="opened_moderation_cases",
    )
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "moderation_case"
        ordering = ("-opened_at",)


class SiteContent(models.Model):
    class ContentType(models.TextChoices):
        FAQ = "faq", "FAQ"
        ANNOUNCEMENT = "announcement", "Announcement"
        HELP_PAGE = "help_page", "Help page"
        LEGAL = "legal", "Legal"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.CharField(max_length=64, choices=ContentType.choices)
    slug = models.SlugField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_published = models.BooleanField(default=False)
    updated_by_admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name="updated_site_content",
    )
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "site_content"
        ordering = ("content_type", "slug")

