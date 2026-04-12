from django.contrib import admin

from .models import AssessmentAnswer, AssessmentQuestion, AssessmentSession, AssessmentTemplate


@admin.register(AssessmentTemplate)
class AssessmentTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "title")


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ("template", "order_index", "response_format")
    list_filter = ("response_format",)
    search_fields = ("question_text",)


@admin.register(AssessmentSession)
class AssessmentSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "template", "status", "total_score", "severity_level", "started_at")
    list_filter = ("status", "severity_level")


@admin.register(AssessmentAnswer)
class AssessmentAnswerAdmin(admin.ModelAdmin):
    list_display = ("session", "question", "answer_value", "answered_at")

