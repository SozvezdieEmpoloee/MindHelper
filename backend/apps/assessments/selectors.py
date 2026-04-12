from django.db.models import Count, Q

from .models import AssessmentSession, AssessmentTemplate


def get_active_templates():
    return AssessmentTemplate.objects.filter(is_active=True).prefetch_related("questions")


def get_user_assessment_stats(user):
    return AssessmentSession.objects.filter(user=user).aggregate(
        total_sessions=Count("id"),
        completed_sessions=Count("id", filter=Q(status=AssessmentSession.Status.COMPLETED)),
    )

