from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import AssessmentAnswer, AssessmentQuestion, AssessmentSession, AssessmentTemplate


def _severity_from_ratio(ratio: Decimal | None) -> str:
    if ratio is None:
        return ""
    if ratio < Decimal("0.25"):
        return "low"
    if ratio < Decimal("0.50"):
        return "moderate"
    if ratio < Decimal("0.75"):
        return "high"
    return "critical"


@transaction.atomic
def start_assessment_session(*, user, template: AssessmentTemplate, chat=None) -> AssessmentSession:
    return AssessmentSession.objects.create(
        user=user,
        chat=chat,
        template=template,
        status=AssessmentSession.Status.STARTED,
    )


@transaction.atomic
def record_answer(
    *,
    session: AssessmentSession,
    question: AssessmentQuestion,
    answer_value=None,
    answer_text: str = "",
) -> AssessmentAnswer:
    answer, _ = AssessmentAnswer.objects.update_or_create(
        session=session,
        question=question,
        defaults={
            "answer_value": answer_value,
            "answer_text": answer_text,
            "answered_at": timezone.now(),
        },
    )
    return answer


@transaction.atomic
def complete_assessment_session(*, session: AssessmentSession) -> AssessmentSession:
    numeric_answers = [
        value
        for value in session.answers.values_list("answer_value", flat=True)
        if value is not None
    ]
    total_score = sum(numeric_answers, Decimal("0"))

    max_score = Decimal("0")
    for question in session.template.questions.all():
        if question.max_value is not None:
            max_score += question.max_value

    ratio = (total_score / max_score) if max_score else None
    session.total_score = total_score
    session.severity_level = _severity_from_ratio(ratio)
    session.status = AssessmentSession.Status.COMPLETED
    session.completed_at = timezone.now()
    session.save(update_fields=("total_score", "severity_level", "status", "completed_at"))
    return session

