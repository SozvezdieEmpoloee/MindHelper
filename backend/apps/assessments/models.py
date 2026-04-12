import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class AssessmentTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "assessment_template"
        ordering = ("title",)

    def __str__(self) -> str:
        return self.title


class AssessmentQuestion(models.Model):
    class ResponseFormat(models.TextChoices):
        SCALE = "scale", "Scale"
        TEXT = "text", "Text"
        NUMBER = "number", "Number"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        AssessmentTemplate,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question_text = models.TextField()
    response_format = models.CharField(max_length=32, choices=ResponseFormat.choices)
    min_value = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    max_value = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    order_index = models.IntegerField()

    class Meta:
        db_table = "assessment_question"
        ordering = ("order_index",)
        constraints = [
            models.UniqueConstraint(
                fields=("template", "order_index"),
                name="uq_template_question_order",
            ),
        ]


class AssessmentSession(models.Model):
    class Status(models.TextChoices):
        STARTED = "started", "Started"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assessment_sessions",
    )
    chat = models.ForeignKey(
        "chat.UserChat",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="assessment_sessions",
    )
    template = models.ForeignKey(
        AssessmentTemplate,
        on_delete=models.RESTRICT,
        related_name="sessions",
    )
    status = models.CharField(max_length=32, choices=Status.choices)
    total_score = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    severity_level = models.CharField(max_length=32, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "assessment_session"
        ordering = ("-started_at",)


class AssessmentAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        AssessmentSession,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        AssessmentQuestion,
        on_delete=models.RESTRICT,
        related_name="answers",
    )
    answer_value = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    answer_text = models.TextField(blank=True)
    answered_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "assessment_answer"
        constraints = [
            models.UniqueConstraint(
                fields=("session", "question"),
                name="uq_session_question",
            ),
        ]

