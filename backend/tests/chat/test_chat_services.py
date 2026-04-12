import pytest

from apps.chat.models import CrisisEvent
from apps.chat.services import create_chat_message, get_or_create_user_chat, register_crisis_event


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

