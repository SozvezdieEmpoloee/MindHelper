from .models import SafetyAuditLog


def create_safety_audit_log(
    *,
    chat,
    message,
    crisis_event,
    model_version,
    assessment,
    decision,
    generated_with_model: bool,
    policy_intervened: bool,
    model_provider: str,
):
    return SafetyAuditLog.objects.create(
        chat=chat,
        message=message,
        crisis_event=crisis_event,
        model_version=model_version,
        risk_level=decision.risk_level,
        route_code=decision.route_code,
        escalation_action=decision.escalation_action,
        human_review_flag=decision.requires_human_review,
        generated_with_model=generated_with_model,
        policy_intervened=policy_intervened,
        model_provider=model_provider,
        matched_rules=list(getattr(assessment, "matched_rules", []) or []),
        action_note=decision.action_note,
    )
