from django.db import transaction
from django.utils import timezone

from apps.directory.models import EmergencyResource
from apps.platform_ops.models import NeuralModelVersion

from .models import ChatMessage, CrisisEvent, UserChat


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


def estimate_risk_score(content_text: str) -> float:
    normalized_text = content_text.lower()
    critical_markers = (
        "suicide",
        "kill myself",
        "harm myself",
        "i do not want to live",
        "не хочу жить",
        "поконч",
        "суицид",
        "навредить себе",
        "убить себя",
    )
    high_markers = (
        "panic",
        "urgent help",
        "very anxious",
        "тревог",
        "паник",
        "страшно",
        "нужна помощь",
        "мне плохо",
    )

    if any(marker in normalized_text for marker in critical_markers):
        return 0.95
    if any(marker in normalized_text for marker in high_markers):
        return 0.72
    return 0.18


def build_bot_reply(content_text: str, risk_score: float) -> str:
    if risk_score >= 0.9:
        return (
            "Мне очень жаль, что вам сейчас так тяжело. Если есть риск немедленно навредить себе "
            "или рядом никого нет, пожалуйста, срочно позвоните в экстренную службу или на линию "
            "кризисной помощи. Я останусь с вами и помогу сделать следующий шаг."
        )
    if risk_score >= 0.7:
        return (
            "Спасибо, что написали об этом. Давайте немного замедлимся: что произошло недавно, "
            "и насколько сильны эти чувства по шкале от 1 до 10?"
        )
    return (
        "Спасибо, что поделились. Я рядом. Расскажите, пожалуйста, чуть подробнее, что вы "
        "чувствуете в последнее время."
    )


@transaction.atomic
def create_chat_turn(*, chat: UserChat, content_text: str):
    risk_score = estimate_risk_score(content_text)
    user_message = create_chat_message(
        chat=chat,
        sender_role=ChatMessage.SenderRole.USER,
        content_text=content_text,
        risk_score=risk_score,
    )
    bot_message = create_chat_message(
        chat=chat,
        sender_role=ChatMessage.SenderRole.BOT,
        content_text=build_bot_reply(content_text, risk_score),
        risk_score=min(risk_score / 3, 1),
    )

    crisis_event = None
    if risk_score >= 0.9:
        emergency_resource = EmergencyResource.objects.filter(is_active=True).order_by("service_name").first()
        crisis_event = register_crisis_event(
            chat=chat,
            risk_level=CrisisEvent.RiskLevel.CRITICAL,
            trigger_message=user_message,
            emergency_resource=emergency_resource,
            action_note="Автоматическая эскалация сработала по результатам оценки риска.",
        )

    return user_message, bot_message, crisis_event


@transaction.atomic
def register_crisis_event(
    *,
    chat: UserChat,
    risk_level: str,
    trigger_message: ChatMessage | None = None,
    emergency_resource=None,
    action_note: str = "",
) -> CrisisEvent:
    return CrisisEvent.objects.create(
        chat=chat,
        trigger_message=trigger_message,
        emergency_resource=emergency_resource,
        risk_level=risk_level,
        status=CrisisEvent.Status.OPEN,
        action_note=action_note,
    )
