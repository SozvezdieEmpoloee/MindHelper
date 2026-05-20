import pytest
from django.utils import timezone

from apps.accounts.models import ChannelAccount
from apps.chat.services import create_chat_message, get_or_create_user_chat
from apps.directory.models import EmergencyResource
from apps.telegram_bot import services as telegram_services
from apps.telegram_bot.services import (
    get_or_create_telegram_user,
    process_message_update,
    remember_sent_bot_message,
    reset_telegram_chat_history,
)


pytestmark = pytest.mark.django_db


def build_update(*, text: str, chat_type: str = "private", user_id: int = 555001, username: str = "minduser"):
    return {
        "update_id": 101,
        "message": {
            "message_id": 1,
            "text": text,
            "chat": {
                "id": user_id,
                "type": chat_type,
            },
            "from": {
                "id": user_id,
                "username": username,
                "first_name": "Mind",
                "last_name": "User",
            },
        },
    }


def test_get_or_create_telegram_user_creates_user_and_channel():
    user = get_or_create_telegram_user(message_payload=build_update(text="/start")["message"])

    channel_account = ChannelAccount.objects.get(
        channel_type=ChannelAccount.ChannelType.TELEGRAM,
        external_user_id="555001",
    )

    assert user.email.startswith("tg_555001_")
    assert channel_account.user_id == user.id


def test_process_message_update_handles_start_command():
    result = process_message_update(build_update(text="/start"))

    assert result.chat_id == "555001"
    assert "Здравствуйте" in result.response_text
    assert "/help" in result.response_text
    assert "как вы себя чувствуете сегодня" in result.response_text.lower()


def test_process_message_update_rejects_group_chat():
    result = process_message_update(build_update(text="hello", chat_type="group"))

    assert result.chat_id == "555001"
    assert "личном чате" in result.response_text


def test_process_message_update_uses_chat_service_for_regular_messages(monkeypatch):
    monkeypatch.setattr(
        telegram_services,
        "create_chat_turn",
        lambda chat, content_text: (None, type("BotMessage", (), {"content_text": "Ответ модели"})(), None),
    )

    result = process_message_update(build_update(text="Мне тревожно"))

    assert result.chat_id == "555001"
    assert result.response_text == "Ответ модели"
    assert result.user_id is not None


def test_process_message_update_handles_reset_command(monkeypatch, regular_user):
    monkeypatch.setattr(telegram_services, "get_or_create_telegram_user", lambda message_payload: regular_user)
    monkeypatch.setattr(telegram_services, "reset_telegram_chat_history", lambda user: [111, 112])

    result = process_message_update(build_update(text="/reset"))

    assert "История диалога очищена" in result.response_text
    assert result.delete_message_ids == [111, 112]


def test_process_message_update_emergency_uses_database_values():
    EmergencyResource.objects.create(
        region_code="RU",
        service_name="Тестовая горячая линия",
        contact_phone="8 (800) 000-00-00",
        is_active=True,
    )

    result = process_message_update(build_update(text="/emergency"))

    assert "Экстренные контакты помощи" in result.response_text
    assert "Тестовая горячая линия" in result.response_text
    assert "8 (800) 000-00-00" in result.response_text


def test_remember_sent_bot_message_appends_to_channel_log(regular_user):
    channel = ChannelAccount.objects.create(
        user=regular_user,
        channel_type=ChannelAccount.ChannelType.TELEGRAM,
        external_user_id="555001",
        external_chat_id="555001",
    )

    remember_sent_bot_message(user_id=str(regular_user.id), message_id=9001)
    channel.refresh_from_db()

    assert channel.bot_message_log[-1]["message_id"] == 9001


def test_reset_telegram_chat_history_clears_db_history_and_returns_recent_bot_message_ids(regular_user):
    channel = ChannelAccount.objects.create(
        user=regular_user,
        channel_type=ChannelAccount.ChannelType.TELEGRAM,
        external_user_id="555001",
        external_chat_id="555001",
        bot_message_log=[
            {"message_id": 101, "sent_at": timezone.now().isoformat()},
            {"message_id": 102, "sent_at": timezone.now().isoformat()},
        ],
    )
    chat = get_or_create_user_chat(user=regular_user)
    create_chat_message(
        chat=chat,
        sender_role="bot",
        content_text="Старый ответ",
        risk_score=0.1,
    )

    recent_ids = reset_telegram_chat_history(user=regular_user)

    channel.refresh_from_db()
    assert recent_ids == [101, 102]
    assert channel.bot_message_log == []
    assert chat.messages.count() == 0
