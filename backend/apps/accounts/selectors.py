from django.utils import timezone

from django.db.models import Count, Max

from apps.assessments.models import AssessmentSession
from apps.chat.models import UserChat
from apps.directory.models import Appointment


def build_user_dashboard_stats(user):
    chat = UserChat.objects.filter(user=user).first()
    chat_stats = (
        chat.messages.aggregate(
            total_messages=Count("id"),
            last_message_at=Max("created_at"),
        )
        if chat
        else {"total_messages": 0, "last_message_at": None}
    )

    assessment_stats = AssessmentSession.objects.filter(user=user).aggregate(
        total_sessions=Count("id"),
        completed_sessions=Count("id", filter=None),
        last_completed_at=Max("completed_at"),
    )

    next_appointment = (
        Appointment.objects.filter(user=user, start_at__gte=timezone.now())
        .order_by("start_at")
        .values("id", "start_at", "status")
        .first()
    )

    return {
        "chat_id": getattr(chat, "id", None),
        "total_messages": chat_stats["total_messages"] or 0,
        "last_message_at": chat_stats["last_message_at"],
        "assessment_sessions": assessment_stats["total_sessions"] or 0,
        "last_assessment_completed_at": assessment_stats["last_completed_at"],
        "next_appointment": next_appointment,
    }
