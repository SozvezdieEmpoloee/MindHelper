import pytest
from django.core.management import call_command

from apps.platform_ops.models import NeuralModelVersion


pytestmark = pytest.mark.django_db


def test_activate_ollama_model_command_creates_active_version(admin_user):
    call_command(
        "activate_ollama_model",
        version_tag="ollama-qwen3-8b-local-test",
        model_name="Qwen3-8B",
        provider="ollama-local",
        safety_profile="strict-v2",
        admin_email=admin_user.email,
    )

    model_version = NeuralModelVersion.objects.get(version_tag="ollama-qwen3-8b-local-test")
    assert model_version.is_active is True
    assert model_version.provider == "ollama-local"
