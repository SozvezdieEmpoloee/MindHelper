from rest_framework import serializers

from .models import AssessmentAnswer, AssessmentQuestion, AssessmentSession, AssessmentTemplate


class AssessmentQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentQuestion
        fields = (
            "id",
            "question_text",
            "response_format",
            "min_value",
            "max_value",
            "order_index",
        )


class AssessmentTemplateSerializer(serializers.ModelSerializer):
    questions = AssessmentQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = AssessmentTemplate
        fields = ("id", "code", "title", "is_active", "questions")


class AssessmentSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentSession
        fields = (
            "id",
            "user",
            "chat",
            "template",
            "status",
            "total_score",
            "severity_level",
            "started_at",
            "completed_at",
        )
        read_only_fields = ("id", "user", "status", "total_score", "severity_level", "completed_at")


class AssessmentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentAnswer
        fields = ("id", "session", "question", "answer_value", "answer_text", "answered_at")
        read_only_fields = ("id", "answered_at")


class AssessmentAnswerCreateSerializer(serializers.Serializer):
    question = serializers.PrimaryKeyRelatedField(queryset=AssessmentQuestion.objects.all())
    answer_value = serializers.DecimalField(max_digits=10, decimal_places=4, required=False, allow_null=True)
    answer_text = serializers.CharField(required=False, allow_blank=True)
