import pytest

from apps.chat.models import CrisisEvent
from apps.chat.services import create_chat_message, create_chat_turn, get_or_create_user_chat, register_crisis_event
from apps.neural_engine import generation as generation_service


pytestmark = pytest.mark.django_db


def test_get_or_create_user_chat_returns_single_chat(regular_user, model_version):
    first_chat = get_or_create_user_chat(user=regular_user, model_version=model_version)
    second_chat = get_or_create_user_chat(user=regular_user, model_version=model_version)

    assert first_chat.id == second_chat.id


def test_create_message_updates_chat_and_crisis_event(regular_user):
    chat = get_or_create_user_chat(user=regular_user)
    message = create_chat_message(
        chat=chat,
        sender_role="user",
        content_text="I feel unsafe right now.",
        risk_score=0.98,
    )
    event = register_crisis_event(
        chat=chat,
        risk_level=CrisisEvent.RiskLevel.CRITICAL,
        trigger_message=message,
        action_note="Escalated for immediate review.",
    )

    assert message.chat_id == chat.id
    assert event.trigger_message_id == message.id
    assert event.status == CrisisEvent.Status.OPEN


def test_create_chat_turn_uses_ollama_reply(regular_user, settings, monkeypatch):
    settings.LLM_PROVIDER = "ollama"
    settings.LLM_OLLAMA_MODEL = "qwen3:8b"

    def fake_request(_payload):
        return {"message": {"role": "assistant", "content": "Поддерживающий ответ модели"}, "done_reason": "stop"}

    monkeypatch.setattr(generation_service, "_request_ollama_chat", fake_request)

    chat = get_or_create_user_chat(user=regular_user)
    _, bot_message, crisis_event = create_chat_turn(
        chat=chat,
        content_text="Сегодня у меня был сложный день.",
    )

    assert "Поддерживающий ответ модели" in bot_message.content_text
    assert crisis_event is None


def test_create_chat_turn_falls_back_when_ollama_fails(regular_user, settings, monkeypatch):
    settings.LLM_PROVIDER = "ollama"

    def fake_request(_payload):
        raise ValueError("network failure")

    monkeypatch.setattr(generation_service, "_request_ollama_chat", fake_request)

    chat = get_or_create_user_chat(user=regular_user)
    _, bot_message, crisis_event = create_chat_turn(
        chat=chat,
        content_text="Мне трудно собраться с мыслями.",
    )

    assert "Спасибо, что написали" in bot_message.content_text
    assert crisis_event is None


def test_high_risk_message_starts_asq_screening(regular_user):
    chat = get_or_create_user_chat(user=regular_user)

    _, bot_message, crisis_event = create_chat_turn(
        chat=chat,
        content_text="У меня бывают мысли о самоубийстве.",
    )

    assert crisis_event is not None
    assert crisis_event.risk_level == "high"
    assert crisis_event.screening_status == CrisisEvent.ScreeningStatus.PENDING
    assert crisis_event.screening_question_index == 1
    assert "вам хотелось, чтобы вы были мертвы" in bot_message.content_text.lower()


def test_critical_method_message_returns_emergency_reply_without_model(regular_user, settings, monkeypatch):
    settings.LLM_PROVIDER = "ollama"

    def fake_request(_payload):
        pytest.fail("Model should not be called for immediate emergency scenarios.")

    monkeypatch.setattr(generation_service, "_request_ollama_chat", fake_request)

    chat = get_or_create_user_chat(user=regular_user)
    _, bot_message, crisis_event = create_chat_turn(
        chat=chat,
        content_text="Я сейчас пойду ложиться на рельсы, чтобы меня переехал поезд.",
    )

    assert crisis_event is not None
    assert crisis_event.risk_level == CrisisEvent.RiskLevel.CRITICAL
    assert crisis_event.screening_status == CrisisEvent.ScreeningStatus.COMPLETED
    assert "Сейчас важнее всего безопасность" in bot_message.content_text


def test_asq_screening_positive_current_thoughts_escalates_to_critical(regular_user):
    chat = get_or_create_user_chat(user=regular_user)

    create_chat_turn(chat=chat, content_text="У меня бывают мысли о самоубийстве.")
    create_chat_turn(chat=chat, content_text="да")
    create_chat_turn(chat=chat, content_text="да")
    create_chat_turn(chat=chat, content_text="да")
    create_chat_turn(chat=chat, content_text="да")
    _, bot_message, crisis_event = create_chat_turn(chat=chat, content_text="да")

    assert crisis_event is not None
    assert crisis_event.risk_level == "critical"
    assert crisis_event.screening_status == CrisisEvent.ScreeningStatus.COMPLETED
    assert "Сейчас важнее всего безопасность" in bot_message.content_text


def test_asq_screening_handles_yes_with_extra_words(regular_user):
    chat = get_or_create_user_chat(user=regular_user)

    create_chat_turn(chat=chat, content_text="У меня бывают мысли о самоубийстве.")
    _, bot_message, crisis_event = create_chat_turn(chat=chat, content_text="да, такое бывало")

    assert crisis_event is not None
    assert crisis_event.screening_question_index == 2
    assert "вам или вашей семье" in bot_message.content_text.lower()


def test_response_policy_replaces_unsafe_model_output(regular_user, settings, monkeypatch):
    settings.LLM_PROVIDER = "ollama"

    def fake_request(_payload):
        return {
            "message": {
                "role": "assistant",
                "content": "Я ставлю вам диагноз и советую начать принимать лекарства немедленно.",
            },
            "done_reason": "stop",
        }

    monkeypatch.setattr(generation_service, "_request_ollama_chat", fake_request)

    chat = get_or_create_user_chat(user=regular_user)
    _, bot_message, _ = create_chat_turn(chat=chat, content_text="Мне просто хочется поговорить.")

    assert "Я не могу ставить диагнозы" in bot_message.content_text
