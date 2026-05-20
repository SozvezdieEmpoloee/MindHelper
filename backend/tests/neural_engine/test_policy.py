import pytest

from apps.neural_engine.policy import (
    SafetyRiskLevel,
    apply_response_policy,
    assess_user_message,
    build_asq_prompt,
    build_asq_repeat_prompt,
    extract_safety_features,
    has_self_harm_signal,
    parse_yes_no_answer,
)
from apps.neural_engine.safety_scenarios import (
    CRITICAL_SCENARIOS,
    ELEVATED_SCENARIOS,
    HIGH_SCENARIOS,
    NON_CRISIS_SCENARIOS,
)


def test_assess_user_message_marks_critical_messages():
    assessment = assess_user_message("Я не хочу жить и думаю убить себя прямо сейчас.")

    assert assessment.risk_level == SafetyRiskLevel.CRITICAL
    assert assessment.immediate_emergency is True
    assert assessment.requires_screening is False
    assert assessment.matched_rules


def test_assess_user_message_marks_high_risk_messages_for_screening():
    assessment = assess_user_message("У меня часто бывают мысли о самоубийстве.")

    assert assessment.risk_level == SafetyRiskLevel.HIGH
    assert assessment.immediate_emergency is False
    assert assessment.requires_screening is True


def test_assess_user_message_marks_elevated_messages():
    assessment = assess_user_message("У меня сильная тревога и я почти не сплю.")

    assert assessment.risk_level == SafetyRiskLevel.ELEVATED
    assert assessment.requires_screening is False


@pytest.mark.parametrize(
    "message",
    CRITICAL_SCENARIOS,
)
def test_assess_user_message_marks_many_critical_scenarios(message):
    assessment = assess_user_message(message)

    assert assessment.risk_level == SafetyRiskLevel.CRITICAL
    assert assessment.immediate_emergency is True
    assert assessment.requires_screening is False
    assert assessment.matched_rules


@pytest.mark.parametrize(
    "message",
    HIGH_SCENARIOS,
)
def test_assess_user_message_marks_many_high_risk_scenarios(message):
    assessment = assess_user_message(message)

    assert assessment.risk_level == SafetyRiskLevel.HIGH
    assert assessment.immediate_emergency is False
    assert assessment.requires_screening is True
    assert assessment.matched_rules


@pytest.mark.parametrize(
    "message",
    ELEVATED_SCENARIOS,
)
def test_assess_user_message_marks_many_elevated_scenarios(message):
    assessment = assess_user_message(message)

    assert assessment.risk_level == SafetyRiskLevel.ELEVATED
    assert assessment.immediate_emergency is False
    assert assessment.requires_screening is False


@pytest.mark.parametrize(
    "message",
    NON_CRISIS_SCENARIOS,
)
def test_assess_user_message_avoids_low_risk_false_negatives_and_non_user_context(message):
    assessment = assess_user_message(message)

    assert assessment.risk_level in {SafetyRiskLevel.LOW, SafetyRiskLevel.ELEVATED}


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Я сейчас пойду ложиться на рельсы, чтобы меня переехал поезд.", True),
        ("Сегодня собираюсь прыгнуть с крыши.", True),
        ("Мне тревожно и тяжело.", False),
        ("Могу пойти приготовить себе ужин.", False),
    ],
)
def test_has_self_harm_signal_detects_dangerous_content(message, expected):
    assert has_self_harm_signal(message) is expected


def test_extract_safety_features_generalizes_beyond_exact_patterns():
    features = extract_safety_features("Мне кажется, я скоро полезу под электричку.")

    assert features.method
    assert features.intent or features.immediacy
    assert not features.third_party_context


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("да", True),
        ("да, такое бывало", True),
        ("нет", False),
        ("нет, не было", False),
        ("не знаю", None),
    ],
)
def test_parse_yes_no_answer_handles_short_russian_replies(value, expected):
    assert parse_yes_no_answer(value) is expected


def test_asq_prompts_are_human_readable():
    first_prompt = build_asq_prompt(1)
    repeat_prompt = build_asq_repeat_prompt(2)

    assert "Чтобы аккуратно оценить уровень риска" in first_prompt
    assert "Пожалуйста, ответьте коротко" in first_prompt
    assert "вам или вашей семье" in repeat_prompt


def test_apply_response_policy_replaces_unsafe_reply():
    safe_reply = apply_response_policy("Я ставлю вам диагноз и советую начать принимать таблетки.")

    assert "Я не могу ставить диагнозы" in safe_reply


def test_apply_response_policy_keeps_safe_reply():
    safe_reply = apply_response_policy("Спасибо, что рассказали об этом. Давайте спокойно разберёмся вместе.")

    assert safe_reply == "Спасибо, что рассказали об этом. Давайте спокойно разберёмся вместе."
