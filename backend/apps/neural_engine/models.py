import uuid

from django.db import models
from django.utils import timezone


class SafetyAuditLog(models.Model):
    class RiskLevel(models.TextChoices):
        LOW = "low", "Low"
        ELEVATED = "elevated", "Elevated"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class RouteCode(models.TextChoices):
        LOW_SUPPORT = "low_support", "Low support"
        ELEVATED_SUPPORT = "elevated_support", "Elevated support"
        IMMEDIATE_EMERGENCY = "immediate_emergency", "Immediate emergency"
        START_SCREENING = "start_screening", "Start screening"
        REPEAT_SCREENING = "repeat_screening", "Repeat screening"
        SCREENING_NEXT_QUESTION = "screening_next_question", "Screening next question"
        SCREENING_NEGATIVE = "screening_negative", "Screening negative"
        SCREENING_HIGH = "screening_high", "Screening high"
        SCREENING_CRITICAL = "screening_critical", "Screening critical"

    class EscalationAction(models.TextChoices):
        NONE = "none", "None"
        OFFER_SPECIALIST = "offer_specialist", "Offer specialist"
        START_ASQ = "start_asq", "Start ASQ"
        URGENT_SPECIALIST = "urgent_specialist", "Urgent specialist"
        EMERGENCY_CONTACTS = "emergency_contacts", "Emergency contacts"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(
        "chat.UserChat",
        on_delete=models.CASCADE,
        related_name="safety_audit_logs",
    )
    message = models.ForeignKey(
        "chat.ChatMessage",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="safety_audit_logs",
    )
    crisis_event = models.ForeignKey(
        "chat.CrisisEvent",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="safety_audit_logs",
    )
    model_version = models.ForeignKey(
        "platform_ops.NeuralModelVersion",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="safety_audit_logs",
    )
    risk_level = models.CharField(max_length=16, choices=RiskLevel.choices)
    route_code = models.CharField(max_length=64, choices=RouteCode.choices)
    escalation_action = models.CharField(max_length=64, choices=EscalationAction.choices)
    human_review_flag = models.BooleanField(default=False)
    generated_with_model = models.BooleanField(default=False)
    policy_intervened = models.BooleanField(default=False)
    model_provider = models.CharField(max_length=64, blank=True)
    matched_rules = models.JSONField(default=list, blank=True)
    action_note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "safety_audit_log"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.route_code} ({self.risk_level})"
