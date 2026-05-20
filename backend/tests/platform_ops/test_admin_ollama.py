import pytest
from django.test import Client
from django.urls import reverse

from apps.platform_ops.models import NeuralModelVersion


pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(admin_user):
    client = Client()
    assert client.login(email=admin_user.email, password="StrongPass123")
    return client


def test_model_versions_changelist_has_ollama_control_button(admin_client):
    url = reverse("admin:platform_ops_neuralmodelversion_changelist")
    response = admin_client.get(url)

    assert response.status_code == 200
    assert b"Ollama Control" in response.content


def test_ollama_control_get_renders_models(admin_client, monkeypatch):
    monkeypatch.setattr(
        "apps.platform_ops.admin.ollama_list_models",
        lambda: [{"name": "qwen3:8b"}],
    )
    url = reverse("admin:platform_ops_neuralmodelversion_ollama_control")
    response = admin_client.get(url)

    assert response.status_code == 200
    assert b"qwen3:8b" in response.content


def test_ollama_control_post_pulls_and_activates(admin_client, admin_user, monkeypatch):
    monkeypatch.setattr("apps.platform_ops.admin.ollama_pull_model", lambda model_name: {"name": model_name})
    monkeypatch.setattr("apps.platform_ops.admin.ollama_list_models", lambda: [{"name": "qwen3:8b"}])

    url = reverse("admin:platform_ops_neuralmodelversion_ollama_control")
    response = admin_client.post(
        url,
        {
            "ollama_model_name": "qwen3:8b",
            "version_tag": "ollama-admin-v1",
            "model_name": "Qwen3-8B",
            "provider": "ollama-local",
            "safety_profile": "strict-v2",
            "pull_before_activate": "on",
        },
        follow=True,
    )

    assert response.status_code == 200
    model = NeuralModelVersion.objects.get(version_tag="ollama-admin-v1")
    assert model.is_active is True
    assert model.created_by_admin_user_id == admin_user.id


def test_admin_action_make_selected_version_active(admin_client, admin_user):
    first = NeuralModelVersion.objects.create(
        version_tag="admin-action-v1",
        model_name="Qwen3-8B",
        provider="ollama-local",
        safety_profile="strict-v1",
        is_active=True,
        created_by_admin_user=admin_user,
    )
    second = NeuralModelVersion.objects.create(
        version_tag="admin-action-v2",
        model_name="Qwen3-8B",
        provider="ollama-local",
        safety_profile="strict-v2",
        is_active=False,
        created_by_admin_user=admin_user,
    )

    url = reverse("admin:platform_ops_neuralmodelversion_changelist")
    response = admin_client.post(
        url,
        {
            "action": "make_selected_version_active",
            "_selected_action": [str(second.id)],
            "index": 0,
            "select_across": 0,
        },
        follow=True,
    )

    assert response.status_code == 200
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.is_active is False
    assert second.is_active is True
