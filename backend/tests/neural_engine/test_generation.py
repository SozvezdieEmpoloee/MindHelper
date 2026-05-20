import json

import pytest

from apps.chat.services import create_chat_message, get_or_create_user_chat
from apps.neural_engine import generation
from apps.neural_engine.policy import SafetyRiskLevel


@pytest.mark.django_db
def test_build_ollama_messages_includes_system_and_history(regular_user):
    chat = get_or_create_user_chat(user=regular_user)
    create_chat_message(chat=chat, sender_role="user", content_text="Мне тревожно.", risk_score=0.5)
    create_chat_message(chat=chat, sender_role="bot", content_text="Я рядом.", risk_score=0.2)

    messages = generation._build_ollama_messages(chat, SafetyRiskLevel.LOW)

    assert messages[0]["role"] == "system"
    assert "не задавай вопрос в каждом ответе автоматически" in messages[0]["content"].lower()
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Мне тревожно."
    assert messages[2]["role"] == "assistant"


def test_deduplicate_repeated_sentences_removes_duplicates():
    text = (
        "Ты не один — такое чувство часто бывает. Попробуй закрыть глаза. "
        "Ты не один — такое чувство часто бывает. Попробуй закрыть глаза."
    )

    result = generation._deduplicate_repeated_sentences(text)

    assert result.count("Ты не один") == 1
    assert result.count("Попробуй закрыть глаза") == 1


def test_detect_scenario_distinguishes_common_cases():
    assert generation._detect_scenario("Мне тревожно и трудно успокоиться") == generation.Scenario.ANXIETY
    assert generation._detect_scenario("Я чувствую сильную усталость") == generation.Scenario.FATIGUE
    assert generation._detect_scenario("Могу пойти приготовить себе ужин") == generation.Scenario.SELF_CARE
    assert generation._detect_scenario("Не могу уснуть уже вторую ночь") == generation.Scenario.SLEEP


def test_looks_like_user_plan_is_disabled_for_self_harm_content():
    assert generation._looks_like_user_plan("Я сейчас пойду ложиться на рельсы, чтобы меня переехал поезд.") is False
    assert generation._looks_like_user_plan("Могу пойти приготовить себе ужин.") is True


def test_looks_truncated_detects_obvious_cutoff():
    assert generation._looks_truncated("Ты не один с этим чувством, но") is True
    assert generation._looks_truncated("Спасибо, что написали. Я рядом.") is False


def test_join_reply_fragments_combines_parts():
    result = generation._join_reply_fragments(
        "Спасибо, что написали. Давайте попроб",
        "уем начать с пары медленных выдохов.",
    )

    assert "Давайте попроб уем" not in result
    assert "Спасибо, что написали." in result
    assert "выдохов" in result


def test_complete_ollama_reply_requests_second_continuation(monkeypatch):
    responses = iter(
        [
            {"message": {"content": "уем начать с пары медленных выдохов, но"}, "done_reason": "length"},
            {"message": {"content": "без попытки сделать всё идеально сразу."}, "done_reason": "stop"},
        ]
    )

    monkeypatch.setattr(generation, "_request_ollama_chat", lambda _payload: next(responses))

    text, done_reason = generation._complete_ollama_reply(
        payload={"messages": [{"role": "system", "content": "test"}]},
        initial_text="Спасибо, что написали. Давайте попроб",
        initial_done_reason="length",
        chat_id="chat-1",
    )

    assert "Давайте попробуем" in text
    assert "без попытки сделать всё идеально сразу." in text
    assert done_reason == "stop"


@pytest.mark.django_db
def test_generate_model_reply_continues_truncated_ollama_response(regular_user, settings, monkeypatch):
    settings.LLM_PROVIDER = "ollama"
    chat = get_or_create_user_chat(user=regular_user)
    create_chat_message(
        chat=chat,
        sender_role="user",
        content_text="Мне тревожно и в голове, и в теле",
        risk_score=0.3,
    )
    calls = {"count": 0}

    def fake_request(payload):
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "message": {
                    "role": "assistant",
                    "content": "Спасибо, что поделились. Когда тяжело и в теле, и в голове — это действительно сложно, но",
                },
                "done_reason": "length",
            }
        assert payload["messages"][-1]["role"] == "user"
        assert "Продолжи свой предыдущий ответ" in payload["messages"][-1]["content"]
        return {
            "message": {
                "role": "assistant",
                "content": "можно начать с нескольких медленных выдохов и небольшого снижения нагрузки на ближайшие минуты.",
            },
            "done_reason": "stop",
        }

    monkeypatch.setattr(generation, "_request_ollama_chat", fake_request)

    result = generation.generate_model_reply(chat=chat, risk_level=SafetyRiskLevel.LOW)

    assert calls["count"] == 2
    assert "Спасибо, что поделились." in result.content_text
    assert "нескольких медленных выдохов" in result.content_text
    assert result.generated_with_model is True
    assert result.policy_intervened is False


@pytest.mark.django_db
def test_generate_model_reply_returns_raw_ollama_response_when_complete(regular_user, settings, monkeypatch):
    settings.LLM_PROVIDER = "ollama"
    chat = get_or_create_user_chat(user=regular_user)
    create_chat_message(chat=chat, sender_role="user", content_text="Могу пойти приготовить себе ужин", risk_score=0.2)

    expected_text = (
        "Да, приготовить себе ужин — это хороший шаг. Лучше выбрать что-то простое и сделать это без спешки."
    )

    def fake_request(_payload):
        return {"message": {"role": "assistant", "content": expected_text}, "done_reason": "stop"}

    monkeypatch.setattr(generation, "_request_ollama_chat", fake_request)

    result = generation.generate_model_reply(chat=chat, risk_level=SafetyRiskLevel.LOW)

    assert result.content_text == expected_text
    assert result.generated_with_model is True
    assert result.policy_intervened is False


@pytest.mark.django_db
def test_generate_model_reply_falls_back_to_policy_safe_reply(regular_user, settings, monkeypatch):
    settings.LLM_PROVIDER = "ollama"
    chat = get_or_create_user_chat(user=regular_user)

    def fake_request(_payload):
        return {
            "message": {
                "role": "assistant",
                "content": "Я ставлю вам диагноз и советую начать принимать лекарства.",
            },
            "done_reason": "stop",
        }

    monkeypatch.setattr(generation, "_request_ollama_chat", fake_request)

    result = generation.generate_model_reply(chat=chat, risk_level=SafetyRiskLevel.LOW)

    assert "Я не могу ставить диагнозы" in result.content_text
    assert result.policy_intervened is True


@pytest.mark.django_db
def test_generate_model_reply_falls_back_when_ollama_errors(regular_user, settings, monkeypatch):
    settings.LLM_PROVIDER = "ollama"
    chat = get_or_create_user_chat(user=regular_user)
    create_chat_message(chat=chat, sender_role="user", content_text="Мне тревожно", risk_score=0.2)

    def fake_request(_payload):
        raise ValueError("network issue")

    monkeypatch.setattr(generation, "_request_ollama_chat", fake_request)

    result = generation.generate_model_reply(chat=chat, risk_level=SafetyRiskLevel.ELEVATED)

    assert "вам сейчас правда тяжело" in result.content_text.lower()
    assert result.generated_with_model is False


def test_request_ollama_chat_uses_json_payload(monkeypatch, settings):
    settings.LLM_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
    settings.LLM_OLLAMA_TIMEOUT_SECONDS = 5
    captured = {}

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"message": {"content": "ok"}, "done_reason": "stop"}).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return DummyResponse()

    monkeypatch.setattr(generation.urllib_request, "urlopen", fake_urlopen)

    payload = {"model": "qwen3:8b", "messages": [{"role": "system", "content": "test"}], "stream": False}
    response = generation._request_ollama_chat(payload)

    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["method"] == "POST"
    assert captured["timeout"] == 5
    assert captured["body"]["model"] == "qwen3:8b"
    assert response["message"]["content"] == "ok"


@pytest.mark.django_db
def test_generate_model_reply_uses_extended_num_predict_budget(regular_user, settings, monkeypatch):
    settings.LLM_PROVIDER = "ollama"
    settings.LLM_MAX_OUTPUT_TOKENS = 280
    chat = get_or_create_user_chat(user=regular_user)
    create_chat_message(
        chat=chat,
        sender_role="user",
        content_text="Мне тревожно и тяжело успокоиться",
        risk_score=0.3,
    )
    captured = {}

    def fake_request(payload):
        captured["payload"] = payload
        return {
            "message": {
                "role": "assistant",
                "content": "Понимаю. Попробуйте сделать несколько медленных выдохов.",
            },
            "done_reason": "stop",
        }

    monkeypatch.setattr(generation, "_request_ollama_chat", fake_request)

    generation.generate_model_reply(chat=chat, risk_level=SafetyRiskLevel.LOW)

    assert captured["payload"]["options"]["num_predict"] >= 640
