from django.contrib import admin

from .models import ChatMessage, CrisisEvent, UserChat


@admin.register(UserChat)
class UserChatAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "model_version", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("user__email", "user__display_name")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("chat", "sender_role", "risk_score", "created_at")
    list_filter = ("sender_role",)
    search_fields = ("content_text", "chat__user__email")


@admin.register(CrisisEvent)
class CrisisEventAdmin(admin.ModelAdmin):
    list_display = ("chat", "risk_level", "status", "detected_at", "resolved_at")
    list_filter = ("risk_level", "status")

