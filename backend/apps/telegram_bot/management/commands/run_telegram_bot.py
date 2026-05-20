from django.core.management.base import BaseCommand, CommandError

from apps.telegram_bot.services import TelegramBotError, delete_webhook, get_me, run_polling_loop


class Command(BaseCommand):
    help = "Run MindHelper Telegram bot using Telegram Bot API long polling."

    def handle(self, *args, **options):
        try:
            bot_info = get_me()
        except TelegramBotError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Telegram bot is starting for @{bot_info.get('username', 'unknown_bot')}"
            )
        )

        try:
            delete_webhook()
            run_polling_loop()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Telegram bot stopped by user."))
