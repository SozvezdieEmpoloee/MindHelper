from django.core.management.base import BaseCommand, CommandError

from apps.telegram_bot.services import (
    TelegramBotError,
    build_default_bot_profile,
    get_me,
    set_bot_commands,
    set_bot_profile,
)


class Command(BaseCommand):
    help = "Configure Telegram bot profile and command list."

    def handle(self, *args, **options):
        profile = build_default_bot_profile()
        try:
            bot_info = get_me()
            set_bot_profile(
                name=profile["name"],
                description=profile["description"],
                short_description=profile["short_description"],
            )
            set_bot_commands()
        except TelegramBotError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Configured Telegram bot profile for @{bot_info.get('username', 'unknown_bot')}"
            )
        )
