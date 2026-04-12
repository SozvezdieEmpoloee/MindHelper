from apps.accounts.models import UserAccount
from apps.chat.models import ChatMessage, CrisisEvent, UserChat
from apps.directory.models import Appointment

from .models import NeuralModelVersion


def build_admin_dashboard_stats():
    active_model = (
        NeuralModelVersion.objects.filter(is_active=True)
        .values("id", "version_tag", "model_name", "provider", "deployed_at")
        .first()
    )

    return {
        "users_total": UserAccount.objects.count(),
        "active_chats": UserChat.objects.filter(status=UserChat.Status.ACTIVE).count(),
        "messages_total": ChatMessage.objects.count(),
        "open_crisis_events": CrisisEvent.objects.filter(status=CrisisEvent.Status.OPEN).count(),
        "appointments_total": Appointment.objects.count(),
        "active_model": active_model,
    }

