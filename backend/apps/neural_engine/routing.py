from dataclasses import dataclass, field
from typing import Any

from django.utils import timezone

from apps.chat.models import CrisisEvent

from .policy import (
    SafetyAssessment,
    SafetyRiskLevel,
    apply_response_policy,
    assess_user_message,
    build_acute_positive_reply,
    build_asq_prompt,
    build_asq_repeat_prompt,
    build_negative_screen_reply,
    build_non_acute_positive_reply,
    parse_yes_no_answer,
)


DEFAULT_POLICY_FALLBACK = (
    "Я рядом и готов помочь вам описать состояние и выбрать безопасный следующий шаг. "
    "Если вы чувствуете угрозу для своей безопасности, лучше сразу обратиться к экстренной помощи."
)

ELEVATED_GUIDANCE_SUFFIX = (
    "Если это состояние держится дольше обычного или усиливается, пожалуйста, подумайте о разговоре со специалистом очно."
)


class RouteCode:
    LOW_SUPPORT = "low_support"
    ELEVATED_SUPPORT = "elevated_support"
    IMMEDIATE_EMERGENCY = "immediate_emergency"
    START_SCREENING = "start_screening"
    REPEAT_SCREENING = "repeat_screening"
    SCREENING_NEXT_QUESTION = "screening_next_question"
    SCREENING_NEGATIVE = "screening_negative"
    SCREENING_HIGH = "screening_high"
    SCREENING_CRITICAL = "screening_critical"


class EscalationAction:
    NONE = "none"
    OFFER_SPECIALIST = "offer_specialist"
    START_ASQ = "start_asq"
    EMERGENCY_CONTACTS = "emergency_contacts"
    URGENT_SPECIALIST = "urgent_specialist"


@dataclass(slots=True)
class SafetyRouteDecision:
    risk_level: str
    route_code: str
    escalation_action: str
    action_note: str
    response_text: str | None = None
    should_generate_model_reply: bool = False
    create_crisis_event: bool = False
    crisis_status: str = CrisisEvent.Status.OPEN
    screening_status: str = CrisisEvent.ScreeningStatus.NOT_REQUIRED
    screening_question_index: int = 0
    screening_answers: list[dict[str, Any]] = field(default_factory=list)
    emergency_resource: Any = None
    requires_human_review: bool = False
    risk_score_override: float | None = None


class CrisisRoutingService:
    def __init__(self, *, emergency_resource=None, emergency_resources_text: str = ""):
        self.emergency_resource = emergency_resource
        self.emergency_resources_text = emergency_resources_text

    def route_message(
        self,
        *,
        content_text: str,
        assessment: SafetyAssessment | None = None,
    ) -> tuple[SafetyAssessment, SafetyRouteDecision]:
        assessment = assessment or assess_user_message(content_text)

        if assessment.immediate_emergency:
            return assessment, SafetyRouteDecision(
                risk_level=SafetyRiskLevel.CRITICAL,
                route_code=RouteCode.IMMEDIATE_EMERGENCY,
                escalation_action=EscalationAction.EMERGENCY_CONTACTS,
                action_note="Критический риск определён правиловым safety-контуром до генерации ответа.",
                response_text=build_acute_positive_reply(self.emergency_resources_text),
                create_crisis_event=True,
                screening_status=CrisisEvent.ScreeningStatus.COMPLETED,
                emergency_resource=self.emergency_resource,
                requires_human_review=True,
                risk_score_override=0.98,
            )

        if assessment.requires_screening:
            return assessment, SafetyRouteDecision(
                risk_level=SafetyRiskLevel.HIGH,
                route_code=RouteCode.START_SCREENING,
                escalation_action=EscalationAction.START_ASQ,
                action_note="Запущен ASQ-скрининг после обнаружения high-risk маркеров в сообщении.",
                response_text=build_asq_prompt(1),
                create_crisis_event=True,
                screening_status=CrisisEvent.ScreeningStatus.PENDING,
                screening_question_index=1,
                emergency_resource=self.emergency_resource,
                risk_score_override=0.65,
            )

        if assessment.risk_level == SafetyRiskLevel.ELEVATED:
            return assessment, SafetyRouteDecision(
                risk_level=SafetyRiskLevel.ELEVATED,
                route_code=RouteCode.ELEVATED_SUPPORT,
                escalation_action=EscalationAction.OFFER_SPECIALIST,
                action_note="Обнаружены elevated-risk маркеры: нужен бережный ответ и рекомендация рассмотреть очную помощь.",
                should_generate_model_reply=True,
            )

        return assessment, SafetyRouteDecision(
            risk_level=SafetyRiskLevel.LOW,
            route_code=RouteCode.LOW_SUPPORT,
            escalation_action=EscalationAction.NONE,
            action_note="Критичных признаков не обнаружено, продолжается поддерживающий диалог.",
            should_generate_model_reply=True,
        )

    def route_screening_response(
        self,
        *,
        event: CrisisEvent,
        content_text: str,
    ) -> SafetyRouteDecision:
        answer = parse_yes_no_answer(content_text)
        if answer is None:
            screening_assessment = assess_user_message(content_text)
            if screening_assessment.immediate_emergency:
                return SafetyRouteDecision(
                    risk_level=SafetyRiskLevel.CRITICAL,
                    route_code=RouteCode.SCREENING_CRITICAL,
                    escalation_action=EscalationAction.EMERGENCY_CONTACTS,
                    action_note="Во время ASQ-скрининга пользователь описал непосредственный риск для жизни.",
                    response_text=build_acute_positive_reply(self.emergency_resources_text),
                    crisis_status=CrisisEvent.Status.OPEN,
                    screening_status=CrisisEvent.ScreeningStatus.COMPLETED,
                    emergency_resource=self.emergency_resource,
                    requires_human_review=True,
                    risk_score_override=0.98,
                    screening_answers=list(event.screening_answers or []),
                )

            return SafetyRouteDecision(
                risk_level=event.risk_level,
                route_code=RouteCode.REPEAT_SCREENING,
                escalation_action=EscalationAction.START_ASQ,
                action_note="Скрининг продолжается: ожидался короткий ответ 'да' или 'нет'.",
                response_text=build_asq_repeat_prompt(event.screening_question_index),
                crisis_status=CrisisEvent.Status.OPEN,
                screening_status=CrisisEvent.ScreeningStatus.PENDING,
                screening_question_index=event.screening_question_index,
                emergency_resource=event.emergency_resource,
                risk_score_override=0.2,
                screening_answers=list(event.screening_answers or []),
            )

        answers = list(event.screening_answers or [])
        answers.append(
            {
                "question_index": event.screening_question_index,
                "answer": answer,
                "raw_text": content_text,
                "answered_at": timezone.now().isoformat(),
            }
        )

        if event.screening_question_index < 4:
            next_index = event.screening_question_index + 1
            return SafetyRouteDecision(
                risk_level=SafetyRiskLevel.HIGH,
                route_code=RouteCode.SCREENING_NEXT_QUESTION,
                escalation_action=EscalationAction.START_ASQ,
                action_note=f"ASQ-скрининг продолжается, переход к вопросу {next_index}.",
                response_text=build_asq_prompt(next_index),
                crisis_status=CrisisEvent.Status.OPEN,
                screening_status=CrisisEvent.ScreeningStatus.PENDING,
                screening_question_index=next_index,
                emergency_resource=event.emergency_resource,
                risk_score_override=0.35,
                screening_answers=answers,
            )

        if event.screening_question_index == 4:
            preliminary_positive = any(item["answer"] for item in answers[:4])
            if preliminary_positive:
                return SafetyRouteDecision(
                    risk_level=SafetyRiskLevel.HIGH,
                    route_code=RouteCode.SCREENING_NEXT_QUESTION,
                    escalation_action=EscalationAction.START_ASQ,
                    action_note="Базовые вопросы ASQ дали положительный результат, задаётся острый контрольный вопрос.",
                    response_text=build_asq_prompt(5),
                    crisis_status=CrisisEvent.Status.OPEN,
                    screening_status=CrisisEvent.ScreeningStatus.PENDING,
                    screening_question_index=5,
                    emergency_resource=event.emergency_resource,
                    risk_score_override=0.5,
                    screening_answers=answers,
                )

            return SafetyRouteDecision(
                risk_level=SafetyRiskLevel.LOW,
                route_code=RouteCode.SCREENING_NEGATIVE,
                escalation_action=EscalationAction.NONE,
                action_note="ASQ-скрининг завершён без подтверждения признаков острого суицидального риска.",
                response_text=build_negative_screen_reply(),
                crisis_status=CrisisEvent.Status.DISMISSED,
                screening_status=CrisisEvent.ScreeningStatus.COMPLETED,
                emergency_resource=event.emergency_resource,
                risk_score_override=0.12,
                screening_answers=answers,
            )

        if answer:
            return SafetyRouteDecision(
                risk_level=SafetyRiskLevel.CRITICAL,
                route_code=RouteCode.SCREENING_CRITICAL,
                escalation_action=EscalationAction.EMERGENCY_CONTACTS,
                action_note="Положительный острый ASQ-скрининг: пользователь подтвердил наличие суицидальных мыслей прямо сейчас.",
                response_text=build_acute_positive_reply(self.emergency_resources_text),
                crisis_status=CrisisEvent.Status.OPEN,
                screening_status=CrisisEvent.ScreeningStatus.COMPLETED,
                emergency_resource=self.emergency_resource,
                requires_human_review=True,
                risk_score_override=0.98,
                screening_answers=answers,
            )

        return SafetyRouteDecision(
            risk_level=SafetyRiskLevel.HIGH,
            route_code=RouteCode.SCREENING_HIGH,
            escalation_action=EscalationAction.URGENT_SPECIALIST,
            action_note="Положительный неострый ASQ-скрининг: требуется очная оценка состояния специалистом.",
            response_text=build_non_acute_positive_reply(self.emergency_resources_text),
            crisis_status=CrisisEvent.Status.OPEN,
            screening_status=CrisisEvent.ScreeningStatus.COMPLETED,
            emergency_resource=self.emergency_resource,
            requires_human_review=True,
            risk_score_override=0.78,
            screening_answers=answers,
        )

    def finalize_generated_reply(self, *, decision: SafetyRouteDecision, model_reply: str) -> str:
        safe_reply = apply_response_policy((model_reply or "").strip())
        if not safe_reply:
            safe_reply = DEFAULT_POLICY_FALLBACK
        if decision.route_code == RouteCode.ELEVATED_SUPPORT:
            return f"{safe_reply}\n\n{ELEVATED_GUIDANCE_SUFFIX}"
        return safe_reply
