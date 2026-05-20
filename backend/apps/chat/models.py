import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class UserChat(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
        BLOCKED = "blocked", "Blocked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat",
    )
    model_version = models.ForeignKey(
        "platform_ops.NeuralModelVersion",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="chats",
    )
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_chat"


class ChatMessage(models.Model):
    class SenderRole(models.TextChoices):
        USER = "user", "User"
        BOT = "bot", "Bot"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(UserChat, on_delete=models.CASCADE, related_name="messages")
    sender_role = models.CharField(max_length=16, choices=SenderRole.choices)
    content_text = models.TextField()
    risk_score = models.DecimalField(max_digits=6, decimal_places=5, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "chat_message"
        ordering = ("created_at",)


class CrisisEvent(models.Model):
    class RiskLevel(models.TextChoices):
        LOW = "low", "Low"
        ELEVATED = "elevated", "Elevated"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    class ScreeningStatus(models.TextChoices):
        NOT_REQUIRED = "not_required", "Not required"
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(UserChat, on_delete=models.CASCADE, related_name="crisis_events")
    trigger_message = models.ForeignKey(
        ChatMessage,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="triggered_crisis_events",
    )
    emergency_resource = models.ForeignKey(
        "directory.EmergencyResource",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="crisis_events",
    )
    risk_level = models.CharField(max_length=16, choices=RiskLevel.choices)
    status = models.CharField(max_length=32, choices=Status.choices)
    screening_status = models.CharField(
        max_length=24,
        choices=ScreeningStatus.choices,
        default=ScreeningStatus.NOT_REQUIRED,
    )
    screening_question_index = models.PositiveSmallIntegerField(default=0)
    screening_answers = models.JSONField(default=list, blank=True)
    action_note = models.TextField(blank=True)
    detected_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "crisis_event"
        ordering = ("-detected_at",)
