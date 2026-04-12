from django.db.models import Avg, Count, Max

from .models import ChatMessage


def get_user_chat_statistics(user):
    return ChatMessage.objects.filter(chat__user=user).aggregate(
        total_messages=Count("id"),
        average_risk=Avg("risk_score"),
        last_message_at=Max("created_at"),
    )

