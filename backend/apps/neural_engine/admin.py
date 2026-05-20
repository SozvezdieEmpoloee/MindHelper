from django.contrib import admin

from .models import SafetyAuditLog


@admin.register(SafetyAuditLog)
class SafetyAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "chat",
        "risk_level",
        "route_code",
        "escalation_action",
        "human_review_flag",
        "generated_with_model",
        "policy_intervened",
        "model_provider",
    )
    list_filter = (
        "risk_level",
        "route_code",
        "escalation_action",
        "human_review_flag",
        "generated_with_model",
        "policy_intervened",
        "model_provider",
    )
    search_fields = (
        "chat__user__email",
        "chat__user__display_name",
        "message__content_text",
        "action_note",
    )
    list_select_related = ("chat", "chat__user", "message", "crisis_event", "model_version")
