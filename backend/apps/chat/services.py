import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.directory.models import EmergencyResource
from apps.neural_engine.audit import create_safety_audit_log
from apps.neural_engine.generation import generate_model_reply
from apps.neural_engine.policy import assess_user_message
from apps.neural_engine.routing import CrisisRoutingService, SafetyRouteDecision
from apps.platform_ops.models import NeuralModelVersion

from .models import ChatMessage, CrisisEvent, UserChat


logger = logging.getLogger(__name__)


def _to_float(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def get_active_model_version():
    return NeuralModelVersion.objects.filter(is_active=True).order_by("-deployed_at").first()


@transaction.atomic
def get_or_create_user_chat(*, user, model_version=None) -> UserChat:
    resolved_model_version = model_version or get_active_model_version()
    chat, created = UserChat.objects.get_or_create(
        user=user,
        defaults={"model_version": resolved_model_version},
    )
    if not created and resolved_model_version and chat.model_version_id is None:
        chat.model_version = resolved_model_version
        chat.save(update_fields=("model_version", "updated_at"))
    return chat


@transaction.atomic
def create_chat_message(*, chat: UserChat, sender_role: str, content_text: str, risk_score=None):
    message = ChatMessage.objects.create(
        chat=chat,
        sender_role=sender_role,
        content_text=content_text,
        risk_score=risk_score,
    )
    chat.updated_at = timezone.now()
    chat.save(update_fields=("updated_at",))
    return message


def get_primary_emergency_resource():
    return EmergencyResource.objects.filter(is_active=True).order_by("service_name").first()


def build_emergency_resources_text(*, limit: int = 2) -> str:
    resources = list(EmergencyResource.objects.filter(is_active=True).order_by("service_name")[:limit])
    if not resources:
        return "Обратитесь в экстренные службы и свяжитесь с близким человеком рядом."
    return "\n".join(f"- {resource.service_name}: {resource.contact_phone}" for resource in resources)


def build_crisis_router() -> CrisisRoutingService:
    emergency_resource = get_primary_emergency_resource()
    resources_text = build_emergency_resources_text()
    return CrisisRoutingService(
        emergency_resource=emergency_resource,
        emergency_resources_text=resources_text,
    )


def get_pending_screening_event(*, chat: UserChat) -> CrisisEvent | None:
    return (
        CrisisEvent.objects.filter(
            chat=chat,
            status=CrisisEvent.Status.OPEN,
            screening_status=CrisisEvent.ScreeningStatus.PENDING,
        )
        .order_by("-detected_at")
        .first()
    )


@transaction.atomic
def register_crisis_event(
    *,
    chat: UserChat,
    risk_level: str,
    trigger_message: ChatMessage | None = None,
    emergency_resource=None,
    action_note: str = "",
    screening_status: str = CrisisEvent.ScreeningStatus.NOT_REQUIRED,
    screening_question_index: int = 0,
    screening_answers: list | None = None,
) -> CrisisEvent:
    return CrisisEvent.objects.create(
        chat=chat,
        trigger_message=trigger_message,
        emergency_resource=emergency_resource,
        risk_level=risk_level,
        status=CrisisEvent.Status.OPEN,
        screening_status=screening_status,
        screening_question_index=screening_question_index,
        screening_answers=screening_answers or [],
        action_note=action_note,
    )


def apply_route_decision_to_event(*, event: CrisisEvent, decision: SafetyRouteDecision) -> CrisisEvent:
    event.risk_level = decision.risk_level
    event.status = decision.crisis_status
    event.screening_status = decision.screening_status
    event.screening_question_index = decision.screening_question_index
    event.screening_answers = decision.screening_answers
    event.action_note = decision.action_note
    event.emergency_resource = decision.emergency_resource
    event.resolved_at = timezone.now() if decision.crisis_status != CrisisEvent.Status.OPEN else None
    event.save(
        update_fields=(
            "risk_level",
            "status",
            "screening_status",
            "screening_question_index",
            "screening_answers",
            "action_note",
            "emergency_resource",
            "resolved_at",
        )
    )
    return event


@transaction.atomic
def create_chat_turn(*, chat: UserChat, content_text: str):
    router = build_crisis_router()
    assessment = assess_user_message(content_text)
    user_message = create_chat_message(
        chat=chat,
        sender_role=ChatMessage.SenderRole.USER,
        content_text=content_text,
        risk_score=assessment.risk_score,
    )

    pending_screening_event = get_pending_screening_event(chat=chat)
    if pending_screening_event:
        decision = router.route_screening_response(
            event=pending_screening_event,
            content_text=content_text,
        )
        crisis_event = apply_route_decision_to_event(event=pending_screening_event, decision=decision)
    else:
        assessment, decision = router.route_message(
            content_text=content_text,
            assessment=assessment,
        )
        crisis_event = None
        if decision.create_crisis_event:
            crisis_event = register_crisis_event(
                chat=chat,
                risk_level=decision.risk_level,
                trigger_message=user_message,
                emergency_resource=decision.emergency_resource,
                action_note=decision.action_note,
                screening_status=decision.screening_status,
                screening_question_index=decision.screening_question_index,
                screening_answers=decision.screening_answers,
            )

    if decision.should_generate_model_reply:
        generation_result = generate_model_reply(chat=chat, risk_level=decision.risk_level)
        bot_reply = router.finalize_generated_reply(decision=decision, model_reply=generation_result.content_text)
        bot_risk_score = min(_to_float(assessment.risk_score) / 2, 1)
        generated_with_model = generation_result.generated_with_model
        policy_intervened = generation_result.policy_intervened
        model_provider = generation_result.provider_label
    else:
        bot_reply = decision.response_text or ""
        bot_risk_score = decision.risk_score_override
        generated_with_model = False
        policy_intervened = False
        model_provider = ""

    bot_message = create_chat_message(
        chat=chat,
        sender_role=ChatMessage.SenderRole.BOT,
        content_text=bot_reply,
        risk_score=bot_risk_score,
    )
    create_safety_audit_log(
        chat=chat,
        message=user_message,
        crisis_event=crisis_event,
        model_version=chat.model_version,
        assessment=assessment,
        decision=decision,
        generated_with_model=generated_with_model,
        policy_intervened=policy_intervened,
        model_provider=model_provider,
    )
    return user_message, bot_message, crisis_event
