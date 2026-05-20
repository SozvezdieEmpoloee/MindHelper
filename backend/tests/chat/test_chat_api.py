import pytest
from rest_framework.test import APIClient


pytestmark = pytest.mark.django_db


def test_post_chat_message_returns_user_and_bot_messages(regular_user, model_version):
    client = APIClient()
    client.force_authenticate(user=regular_user)

    response = client.post(
        "/api/v1/chat/messages/",
        {"content_text": "I feel very anxious today."},
        format="json",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["user_message"]["sender_role"] == "user"
    assert payload["bot_message"]["sender_role"] == "bot"
    assert payload["crisis_event"] is None


def test_high_risk_message_creates_crisis_event(regular_user):
    client = APIClient()
    client.force_authenticate(user=regular_user)

    response = client.post(
        "/api/v1/chat/messages/",
        {"content_text": "I do not want to live and I might harm myself."},
        format="json",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["crisis_event"] is not None
    assert payload["crisis_event"]["risk_level"] == "critical"


def test_suicidal_ideation_starts_screening_flow(regular_user):
    client = APIClient()
    client.force_authenticate(user=regular_user)

    response = client.post(
        "/api/v1/chat/messages/",
        {"content_text": "У меня бывают мысли о самоубийстве."},
        format="json",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["crisis_event"] is not None
    assert payload["crisis_event"]["risk_level"] == "high"
    assert "ответьте коротко" in payload["bot_message"]["content_text"].lower()
