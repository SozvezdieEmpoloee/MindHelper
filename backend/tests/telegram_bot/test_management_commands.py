import pytest
from django.core.management import call_command


pytestmark = pytest.mark.django_db


def test_configure_telegram_bot_command(monkeypatch):
    monkeypatch.setattr(
        "apps.telegram_bot.management.commands.configure_telegram_bot.get_me",
        lambda: {"username": "mindhelper_support_bot"},
    )
    monkeypatch.setattr(
        "apps.telegram_bot.management.commands.configure_telegram_bot.set_bot_profile",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "apps.telegram_bot.management.commands.configure_telegram_bot.set_bot_commands",
        lambda: None,
    )

    call_command("configure_telegram_bot")


def test_run_telegram_bot_command(monkeypatch):
    monkeypatch.setattr(
        "apps.telegram_bot.management.commands.run_telegram_bot.get_me",
        lambda: {"username": "mindhelper_support_bot"},
    )
    monkeypatch.setattr(
        "apps.telegram_bot.management.commands.run_telegram_bot.delete_webhook",
        lambda: None,
    )
    monkeypatch.setattr(
        "apps.telegram_bot.management.commands.run_telegram_bot.run_polling_loop",
        lambda: None,
    )

    call_command("run_telegram_bot")
