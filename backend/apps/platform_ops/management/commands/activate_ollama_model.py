from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.platform_ops.services import resolve_admin_user, upsert_and_activate_model_version


class Command(BaseCommand):
    help = "Upserts and activates the current Ollama model version in neural_model_version."

    def add_arguments(self, parser):
        parser.add_argument("--version-tag", dest="version_tag", default=settings.LLM_MODEL_VERSION_TAG)
        parser.add_argument("--model-name", dest="model_name", default=settings.LLM_MODEL_DISPLAY_NAME)
        parser.add_argument("--provider", dest="provider", default=settings.LLM_PROVIDER_LABEL)
        parser.add_argument("--safety-profile", dest="safety_profile", default=settings.LLM_SAFETY_PROFILE)
        parser.add_argument("--admin-email", dest="admin_email", default=settings.LLM_ADMIN_EMAIL)

    def handle(self, *args, **options):
        version_tag = options["version_tag"]
        model_name = options["model_name"]
        provider = options["provider"]
        safety_profile = options["safety_profile"]
        admin_email = options["admin_email"]

        try:
            admin_user = resolve_admin_user(admin_email=admin_email)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        model_version, created = upsert_and_activate_model_version(
            version_tag=version_tag,
            model_name=model_name,
            provider=provider,
            safety_profile=safety_profile,
            admin_user=admin_user,
        )

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Model version {action}: {model_version.version_tag} "
                f"(provider={model_version.provider}, active={model_version.is_active})"
            )
        )
