import json
import logging
import time
from dataclasses import dataclass, field
from datetime import timedelta
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.accounts.models import ChannelAccount, UserAccount
from apps.chat.services import create_chat_turn, get_or_create_user_chat
from apps.directory.models import EmergencyResource


logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "Здравствуйте. Я бот сервиса MindHelper.\n\n"
    "Я могу поддержать разговор, помочь сориентироваться в самочувствии и подсказать, где искать "
    "помощь. Бот не ставит диагноз и не заменяет экстренную медицинскую помощь. Если есть "
    "непосредственная опасность, используйте команду /emergency."
)

STARTER_PROMPT_TEXT = (
    "Чтобы начать, можно просто написать, как вы себя чувствуете сегодня, "
    "или что сейчас даётся вам тяжелее всего."
)

HELP_TEXT = (
    "Доступные команды:\n"
    "/start - начать работу с ботом\n"
    "/help - показать команды\n"
    "/privacy - как используются данные\n"
    "/emergency - экстренные контакты помощи\n"
    "/reset - очистить сохранённую историю диалога"
)

PRIVACY_TEXT = (
    "MindHelper сохраняет историю диалога в базе данных сервиса, чтобы поддерживать непрерывность "
    "общения, работу модерации и корректную маршрутизацию в кризисных ситуациях. Бот не является "
    "системой медицинской диагностики."
)

GROUP_REJECT_TEXT = "Пожалуйста, используйте этого бота только в личном чате."
TEXT_ONLY_MESSAGE = "Сейчас я принимаю только текстовые сообщения."
UNKNOWN_COMMAND_TEXT = "Неизвестная команда. Используйте /help, чтобы увидеть доступные варианты."
RESET_DONE_TEXT = "История диалога очищена. Последние сообщения бота в Telegram удалены, где это позволил Telegram API."
GENERIC_ERROR_TEXT = "Не удалось обработать сообщение. Попробуйте ещё раз немного позже."


class TelegramBotError(RuntimeError):
    pass


@dataclass(slots=True)
class TelegramUpdateResult:
    response_text: str | None = None
    chat_id: str | None = None
    user_id: str | None = None
    delete_message_ids: list[int] = field(default_factory=list)
    should_continue: bool = True


def _telegram_api_base() -> str:
    return getattr(settings, "TELEGRAM_BOT_API_BASE_URL", "https://api.telegram.org").rstrip("/")


def _telegram_token() -> str:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise TelegramBotError("TELEGRAM_BOT_TOKEN is not configured.")
    return token


def _telegram_request(*, method: str, payload: dict | None = None, timeout: float | None = None) -> dict:
    token = _telegram_token()
    url = f"{_telegram_api_base()}/bot{token}/{method}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib_request.Request(url=url, data=data, method="POST", headers=headers)
    request_timeout = timeout if timeout is not None else float(settings.TELEGRAM_BOT_TIMEOUT_SECONDS)

    try:
        with urllib_request.urlopen(request, timeout=request_timeout) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except (urllib_error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        raise TelegramBotError(str(exc)) from exc

    if not parsed.get("ok", False):
        raise TelegramBotError(parsed.get("description", "Telegram API request failed."))

    return parsed["result"]


def get_updates(*, offset: int | None = None) -> list[dict]:
    payload = {
        "timeout": int(settings.TELEGRAM_BOT_POLL_TIMEOUT_SECONDS),
        "allowed_updates": ["message"],
    }
    if offset is not None:
        payload["offset"] = offset
    return _telegram_request(
        method="getUpdates",
        payload=payload,
        timeout=float(settings.TELEGRAM_BOT_POLL_TIMEOUT_SECONDS) + 5,
    )


def delete_webhook() -> dict:
    return _telegram_request(
        method="deleteWebhook",
        payload={"drop_pending_updates": False},
    )


def send_message(*, chat_id: str | int, text: str) -> dict:
    return _telegram_request(
        method="sendMessage",
        payload={
            "chat_id": chat_id,
            "text": text,
        },
    )


def delete_message(*, chat_id: str | int, message_id: int) -> bool:
    try:
        _telegram_request(
            method="deleteMessage",
            payload={
                "chat_id": chat_id,
                "message_id": message_id,
            },
        )
        return True
    except TelegramBotError as exc:
        logger.info(
            "Telegram message could not be deleted chat_id=%s message_id=%s reason=%s",
            chat_id,
            message_id,
            exc,
        )
        return False


def delete_messages(*, chat_id: str | int, message_ids: list[int]) -> int:
    deleted = 0
    for message_id in sorted(set(message_ids), reverse=True):
        if delete_message(chat_id=chat_id, message_id=message_id):
            deleted += 1
    return deleted


def set_bot_commands() -> None:
    _telegram_request(
        method="setMyCommands",
        payload={
            "commands": [
                {"command": "start", "description": "Начать работу с ботом"},
                {"command": "help", "description": "Показать список команд"},
                {"command": "privacy", "description": "Как используются данные"},
                {"command": "emergency", "description": "Показать контакты экстренной помощи"},
                {"command": "reset", "description": "Очистить сохранённую историю диалога"},
            ]
        },
    )


def set_bot_profile(*, name: str, description: str, short_description: str) -> None:
    _telegram_request(method="setMyName", payload={"name": name})
    _telegram_request(method="setMyDescription", payload={"description": description})
    _telegram_request(method="setMyShortDescription", payload={"short_description": short_description})


def _build_telegram_identity(message_payload: dict) -> tuple[str, str, str]:
    from_user = message_payload.get("from") or {}
    telegram_user_id = str(from_user.get("id"))
    username = from_user.get("username") or telegram_user_id
    first_name = from_user.get("first_name") or "Telegram"
    last_name = from_user.get("last_name") or "User"
    display_name = " ".join(part for part in [first_name, last_name] if part).strip()
    email = f"tg_{telegram_user_id}_{username}@telegram.local".lower()
    return telegram_user_id, display_name[:120], email[:255]


def get_telegram_channel_account(*, user: UserAccount) -> ChannelAccount:
    return ChannelAccount.objects.get(
        user=user,
        channel_type=ChannelAccount.ChannelType.TELEGRAM,
    )


@transaction.atomic
def get_or_create_telegram_user(*, message_payload: dict) -> UserAccount:
    telegram_user_id, display_name, email = _build_telegram_identity(message_payload)
    channel_account = ChannelAccount.objects.select_related("user").filter(
        channel_type=ChannelAccount.ChannelType.TELEGRAM,
        external_user_id=telegram_user_id,
    ).first()
    if channel_account:
        if message_payload.get("chat"):
            chat_id = str(message_payload["chat"].get("id"))
            if channel_account.external_chat_id != chat_id:
                channel_account.external_chat_id = chat_id
                channel_account.save(update_fields=("external_chat_id",))
                logger.info(
                    "Updated Telegram chat binding for user=%s external_user_id=%s chat_id=%s",
                    channel_account.user_id,
                    telegram_user_id,
                    chat_id,
                )
        return channel_account.user

    user = UserAccount.objects.create_user(
        email=email,
        password=None,
        display_name=display_name,
    )
    ChannelAccount.objects.create(
        user=user,
        channel_type=ChannelAccount.ChannelType.TELEGRAM,
        external_user_id=telegram_user_id,
        external_chat_id=str((message_payload.get("chat") or {}).get("id", "")) or None,
        is_active=True,
    )
    logger.info("Created Telegram-linked user=%s external_user_id=%s", user.id, telegram_user_id)
    return user


def build_emergency_text() -> str:
    resources = list(EmergencyResource.objects.filter(is_active=True).order_by("service_name")[:5])
    if not resources:
        return (
            "Если есть непосредственная опасность, срочно обратитесь в экстренные службы и к "
            "близкому человеку, который может быть рядом с вами."
        )

    lines = [
        "Экстренные контакты помощи:",
        "",
    ]
    for resource in resources:
        contact_line = f"- {resource.service_name}: {resource.contact_phone}"
        if resource.contact_url:
            contact_line += f" ({resource.contact_url})"
        lines.append(contact_line)
    return "\n".join(lines)


def _filter_recent_message_ids(log_entries: list[dict]) -> list[int]:
    cutoff = timezone.now() - timedelta(hours=48)
    recent_message_ids: list[int] = []
    for item in log_entries:
        message_id = item.get("message_id")
        sent_at_raw = item.get("sent_at")
        sent_at = parse_datetime(sent_at_raw) if sent_at_raw else None
        if message_id is None or sent_at is None:
            continue
        if sent_at.tzinfo is None:
            sent_at = timezone.make_aware(sent_at, timezone.get_current_timezone())
        if sent_at >= cutoff:
            recent_message_ids.append(int(message_id))
    return recent_message_ids


@transaction.atomic
def remember_sent_bot_message(*, user_id: str, message_id: int) -> None:
    channel_account = ChannelAccount.objects.select_for_update().get(
        user_id=user_id,
        channel_type=ChannelAccount.ChannelType.TELEGRAM,
    )
    message_log = list(channel_account.bot_message_log or [])
    message_log.append(
        {
            "message_id": int(message_id),
            "sent_at": timezone.now().isoformat(),
        }
    )
    channel_account.bot_message_log = message_log[-50:]
    channel_account.save(update_fields=("bot_message_log",))


@transaction.atomic
def reset_telegram_chat_history(*, user: UserAccount) -> list[int]:
    channel_account = get_telegram_channel_account(user=user)
    recent_bot_message_ids = _filter_recent_message_ids(list(channel_account.bot_message_log or []))

    chat = get_or_create_user_chat(user=user)
    deleted_count, _ = chat.messages.all().delete()
    channel_account.bot_message_log = []
    channel_account.save(update_fields=("bot_message_log",))

    logger.info(
        "Telegram chat history reset for user=%s deleted_objects=%s deletable_bot_messages=%s",
        user.id,
        deleted_count,
        len(recent_bot_message_ids),
    )
    return recent_bot_message_ids


def _handle_command(*, command: str, user: UserAccount) -> tuple[str, list[int]]:
    if command == "/start":
        return f"{WELCOME_TEXT}\n\n{HELP_TEXT}\n\n{STARTER_PROMPT_TEXT}", []
    if command == "/help":
        return HELP_TEXT, []
    if command == "/privacy":
        return PRIVACY_TEXT, []
    if command == "/emergency":
        return build_emergency_text(), []
    if command == "/reset":
        return RESET_DONE_TEXT, reset_telegram_chat_history(user=user)
    return UNKNOWN_COMMAND_TEXT, []


def process_message_update(update_payload: dict) -> TelegramUpdateResult:
    message = update_payload.get("message")
    if not message:
        return TelegramUpdateResult()

    chat_payload = message.get("chat") or {}
    chat_type = chat_payload.get("type")
    chat_id = str(chat_payload.get("id"))
    if chat_type != "private":
        logger.warning("Rejected non-private Telegram chat update chat_id=%s chat_type=%s", chat_id, chat_type)
        return TelegramUpdateResult(response_text=GROUP_REJECT_TEXT, chat_id=chat_id)

    text = (message.get("text") or "").strip()
    if not text:
        return TelegramUpdateResult(response_text=TEXT_ONLY_MESSAGE, chat_id=chat_id)

    user = get_or_create_telegram_user(message_payload=message)
    if text.startswith("/"):
        logger.info("Processing Telegram command=%s user=%s", text.split()[0].lower(), user.id)
        response_text, delete_message_ids = _handle_command(command=text.split()[0].lower(), user=user)
        return TelegramUpdateResult(
            response_text=response_text,
            chat_id=chat_id,
            user_id=str(user.id),
            delete_message_ids=delete_message_ids,
        )

    chat = get_or_create_user_chat(user=user)
    logger.info("Processing Telegram message for user=%s chat=%s", user.id, chat.id)
    _, bot_message, _ = create_chat_turn(chat=chat, content_text=text)
    return TelegramUpdateResult(
        response_text=bot_message.content_text,
        chat_id=chat_id,
        user_id=str(user.id),
    )


def run_polling_loop(*, idle_seconds: float = 1.0) -> None:
    offset = None
    logger.info("Telegram bot polling loop started.")
    while True:
        updates = get_updates(offset=offset)
        for update in updates:
            offset = int(update["update_id"]) + 1
            try:
                result = process_message_update(update)
                if result.delete_message_ids and result.chat_id:
                    deleted_count = delete_messages(chat_id=result.chat_id, message_ids=result.delete_message_ids)
                    logger.info(
                        "Deleted Telegram bot messages chat_id=%s deleted_count=%s",
                        result.chat_id,
                        deleted_count,
                    )
                if result.response_text and result.chat_id:
                    sent_message = send_message(chat_id=result.chat_id, text=result.response_text)
                    if result.user_id:
                        remember_sent_bot_message(
                            user_id=result.user_id,
                            message_id=int(sent_message.get("message_id")),
                        )
            except Exception:
                logger.exception("Failed to process Telegram update_id=%s", update.get("update_id"))
                message = update.get("message") or {}
                chat = message.get("chat") or {}
                chat_id = chat.get("id")
                if chat_id:
                    try:
                        send_message(chat_id=chat_id, text=GENERIC_ERROR_TEXT)
                    except TelegramBotError:
                        logger.exception("Failed to send fallback Telegram error message chat_id=%s", chat_id)
        if not updates:
            time.sleep(idle_seconds)


def get_me() -> dict:
    return _telegram_request(method="getMe")


def build_default_bot_profile() -> dict:
    return {
        "name": "MindHelper Поддержка",
        "description": (
            "Поддерживающий чат для предварительной психологической помощи, экстренных контактов "
            "и бережной навигации к специалистам."
        ),
        "short_description": "Поддерживающий чат и контакты экстренной помощи.",
    }
