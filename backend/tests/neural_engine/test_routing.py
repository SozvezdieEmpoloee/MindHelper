import pytest

from apps.chat.models import CrisisEvent
from apps.chat.services import get_or_create_user_chat
from apps.neural_engine.policy import SafetyRiskLevel, assess_user_message
from apps.neural_engine.routing import CrisisRoutingService, EscalationAction, RouteCode


pytestmark = pytest.mark.django_db


@pytest.fixture
def routing_service():
    return CrisisRoutingService(
        emergency_resource=None,
        emergency_resources_text="- Горячая линия: 8 (800) 000-00-00",
    )


def test_route_message_for_low_risk_uses_model_reply(routing_service):
    assessment, decision = routing_service.route_message(content_text="Мне хотелось бы просто поговорить.")

    assert assessment.risk_level == SafetyRiskLevel.LOW
    assert decision.route_code == RouteCode.LOW_SUPPORT
    assert decision.should_generate_model_reply is True
    assert decision.escalation_action == EscalationAction.NONE


def test_route_message_for_elevated_risk_adds_specialist_guidance(routing_service):
    assessment = assess_user_message("У меня сильная тревога и я плохо сплю.")
    _, decision = routing_service.route_message(content_text="У меня сильная тревога и я плохо сплю.", assessment=assessment)

    assert decision.route_code == RouteCode.ELEVATED_SUPPORT
    assert decision.escalation_action == EscalationAction.OFFER_SPECIALIST
    assert decision.should_generate_model_reply is True

    final_reply = routing_service.finalize_generated_reply(
        decision=decision,
        model_reply="Спасибо, что рассказали об этом.",
    )

    assert "Спасибо, что рассказали" in final_reply
    assert "подумайте о разговоре со специалистом очно" in final_reply


def test_route_message_for_critical_risk_returns_emergency_reply(routing_service):
    _, decision = routing_service.route_message(content_text="Я не хочу жить и думаю убить себя прямо сейчас.")

    assert decision.route_code == RouteCode.IMMEDIATE_EMERGENCY
    assert decision.escalation_action == EscalationAction.EMERGENCY_CONTACTS
    assert decision.create_crisis_event is True
    assert decision.requires_human_review is True
    assert "Горячая линия" in decision.response_text


def test_route_message_for_method_and_immediacy_returns_emergency_reply(routing_service):
    _, decision = routing_service.route_message(
        content_text="Я сейчас пойду ложиться на рельсы, чтобы меня переехал поезд.",
    )

    assert decision.route_code == RouteCode.IMMEDIATE_EMERGENCY
    assert decision.escalation_action == EscalationAction.EMERGENCY_CONTACTS
    assert decision.should_generate_model_reply is False
    assert decision.requires_human_review is True


@pytest.mark.django_db
def test_route_screening_response_repeats_question_on_free_text(routing_service, regular_user):
    chat = get_or_create_user_chat(user=regular_user)
    event = CrisisEvent.objects.create(
        chat=chat,
        risk_level=CrisisEvent.RiskLevel.HIGH,
        status=CrisisEvent.Status.OPEN,
        screening_status=CrisisEvent.ScreeningStatus.PENDING,
        screening_question_index=2,
        screening_answers=[],
    )

    decision = routing_service.route_screening_response(event=event, content_text="мне трудно ответить")

    assert decision.route_code == RouteCode.REPEAT_SCREENING
    assert decision.screening_question_index == 2
    assert "короткий ответ" in decision.response_text.lower()


def test_route_screening_response_advances_to_next_question(routing_service, regular_user):
    chat = get_or_create_user_chat(user=regular_user)
    event = CrisisEvent.objects.create(
        chat=chat,
        risk_level=CrisisEvent.RiskLevel.HIGH,
        status=CrisisEvent.Status.OPEN,
        screening_status=CrisisEvent.ScreeningStatus.PENDING,
        screening_question_index=1,
        screening_answers=[],
    )

    decision = routing_service.route_screening_response(event=event, content_text="да")

    assert decision.route_code == RouteCode.SCREENING_NEXT_QUESTION
    assert decision.screening_question_index == 2
    assert len(decision.screening_answers) == 1


def test_route_screening_response_finishes_with_critical_if_current_thoughts_confirmed(routing_service, regular_user):
    chat = get_or_create_user_chat(user=regular_user)
    event = CrisisEvent.objects.create(
        chat=chat,
        risk_level=CrisisEvent.RiskLevel.HIGH,
        status=CrisisEvent.Status.OPEN,
        screening_status=CrisisEvent.ScreeningStatus.PENDING,
        screening_question_index=5,
        screening_answers=[
            {"question_index": 1, "answer": True},
            {"question_index": 2, "answer": True},
            {"question_index": 3, "answer": False},
            {"question_index": 4, "answer": False},
        ],
    )

    decision = routing_service.route_screening_response(event=event, content_text="да")

    assert decision.route_code == RouteCode.SCREENING_CRITICAL
    assert decision.escalation_action == EscalationAction.EMERGENCY_CONTACTS
    assert decision.requires_human_review is True
    assert decision.screening_status == CrisisEvent.ScreeningStatus.COMPLETED


def test_route_screening_response_finishes_with_high_if_not_current_but_positive_history(routing_service, regular_user):
    chat = get_or_create_user_chat(user=regular_user)
    event = CrisisEvent.objects.create(
        chat=chat,
        risk_level=CrisisEvent.RiskLevel.HIGH,
        status=CrisisEvent.Status.OPEN,
        screening_status=CrisisEvent.ScreeningStatus.PENDING,
        screening_question_index=5,
        screening_answers=[
            {"question_index": 1, "answer": False},
            {"question_index": 2, "answer": True},
            {"question_index": 3, "answer": False},
            {"question_index": 4, "answer": False},
        ],
    )

    decision = routing_service.route_screening_response(event=event, content_text="нет")

    assert decision.route_code == RouteCode.SCREENING_HIGH
    assert decision.escalation_action == EscalationAction.URGENT_SPECIALIST
    assert decision.requires_human_review is True
    assert "очная оценка состояния" in decision.response_text.lower()
