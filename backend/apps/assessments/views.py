from rest_framework import generics, permissions, response, views

from .models import AssessmentQuestion, AssessmentSession
from .selectors import get_active_templates
from .serializers import (
    AssessmentAnswerSerializer,
    AssessmentAnswerCreateSerializer,
    AssessmentSessionSerializer,
    AssessmentTemplateSerializer,
)
from .services import complete_assessment_session, record_answer, start_assessment_session


class AssessmentTemplateListAPIView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AssessmentTemplateSerializer

    def get_queryset(self):
        return get_active_templates()


class AssessmentSessionListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AssessmentSessionSerializer

    def get_queryset(self):
        return AssessmentSession.objects.filter(user=self.request.user).select_related("template", "chat")

    def perform_create(self, serializer):
        template = serializer.validated_data["template"]
        chat = serializer.validated_data.get("chat")
        session = start_assessment_session(user=self.request.user, template=template, chat=chat)
        serializer.instance = session


class AssessmentAnswerCreateAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, session_id):
        serializer = AssessmentAnswerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = AssessmentSession.objects.get(id=session_id, user=request.user)
        question = AssessmentQuestion.objects.get(id=serializer.validated_data["question"].id)
        answer = record_answer(
            session=session,
            question=question,
            answer_value=serializer.validated_data.get("answer_value"),
            answer_text=serializer.validated_data.get("answer_text", ""),
        )
        return response.Response(AssessmentAnswerSerializer(answer).data, status=201)


class AssessmentSessionCompleteAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, session_id):
        session = AssessmentSession.objects.get(id=session_id, user=request.user)
        session = complete_assessment_session(session=session)
        return response.Response(AssessmentSessionSerializer(session).data)
