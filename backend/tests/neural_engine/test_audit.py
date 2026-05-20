import pytest

from apps.chat.services import create_chat_turn, get_or_create_user_chat
from apps.neural_engine.models import SafetyAuditLog


pytestmark = pytest.mark.django_db


def test_create_chat_turn_writes_safety_audit_log_for_low_risk(regular_user):
    chat = get_or_create_user_chat(user=regular_user)

    create_chat_turn(chat=chat, content_text="Мне просто хочется поговорить о своём состоянии.")

    audit_log = SafetyAuditLog.objects.get(chat=chat)
    assert audit_log.route_code == SafetyAuditLog.RouteCode.LOW_SUPPORT
    assert audit_log.escalation_action == SafetyAuditLog.EscalationAction.NONE
    assert audit_log.human_review_flag is False


def test_create_chat_turn_writes_safety_audit_log_for_screening_start(regular_user):
    chat = get_or_create_user_chat(user=regular_user)

    _, _, crisis_event = create_chat_turn(chat=chat, content_text="У меня бывают мысли о самоубийстве.")

    audit_log = SafetyAuditLog.objects.filter(chat=chat).latest("created_at")
    assert crisis_event is not None
    assert audit_log.crisis_event_id == crisis_event.id
    assert audit_log.route_code == SafetyAuditLog.RouteCode.START_SCREENING
    assert audit_log.escalation_action == SafetyAuditLog.EscalationAction.START_ASQ
    assert audit_log.human_review_flag is False


def test_create_chat_turn_writes_safety_audit_log_for_critical_route(regular_user):
    chat = get_or_create_user_chat(user=regular_user)

    create_chat_turn(chat=chat, content_text="Я не хочу жить и думаю убить себя прямо сейчас.")

    audit_log = SafetyAuditLog.objects.filter(chat=chat).latest("created_at")
    assert audit_log.route_code == SafetyAuditLog.RouteCode.IMMEDIATE_EMERGENCY
    assert audit_log.escalation_action == SafetyAuditLog.EscalationAction.EMERGENCY_CONTACTS
    assert audit_log.human_review_flag is True
