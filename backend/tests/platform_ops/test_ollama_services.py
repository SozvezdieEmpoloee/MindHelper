import pytest

from apps.platform_ops.services import (
    ollama_list_models,
    resolve_admin_user,
    upsert_and_activate_model_version,
)


pytestmark = pytest.mark.django_db


def test_ollama_list_models_uses_payload_shape(monkeypatch):
    def fake_request(**_kwargs):
        return {"models": [{"name": "qwen3:8b"}, {"name": "phi4:latest"}]}

    monkeypatch.setattr("apps.platform_ops.services._ollama_request", fake_request)
    models = ollama_list_models()

    assert len(models) == 2
    assert models[0]["name"] == "qwen3:8b"


def test_resolve_admin_user_by_email(admin_user):
    resolved = resolve_admin_user(admin_email=admin_user.email)
    assert resolved.id == admin_user.id


def test_upsert_and_activate_model_version_switches_active(admin_user):
    first_version, _ = upsert_and_activate_model_version(
        version_tag="ollama-v1",
        model_name="Qwen3-8B",
        provider="ollama-local",
        safety_profile="strict-v1",
        admin_user=admin_user,
    )
    second_version, created = upsert_and_activate_model_version(
        version_tag="ollama-v2",
        model_name="Qwen3-8B",
        provider="ollama-local",
        safety_profile="strict-v2",
        admin_user=admin_user,
    )

    first_version.refresh_from_db()
    second_version.refresh_from_db()

    assert created is True
    assert first_version.is_active is False
    assert second_version.is_active is True
