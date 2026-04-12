from django.urls import path

from .views import (
    AssessmentAnswerCreateAPIView,
    AssessmentSessionCompleteAPIView,
    AssessmentSessionListCreateAPIView,
    AssessmentTemplateListAPIView,
)


urlpatterns = [
    path("templates/", AssessmentTemplateListAPIView.as_view(), name="assessment-template-list"),
    path("sessions/", AssessmentSessionListCreateAPIView.as_view(), name="assessment-session-list"),
    path(
        "sessions/<uuid:session_id>/answers/",
        AssessmentAnswerCreateAPIView.as_view(),
        name="assessment-answer-create",
    ),
    path(
        "sessions/<uuid:session_id>/complete/",
        AssessmentSessionCompleteAPIView.as_view(),
        name="assessment-session-complete",
    ),
]
