from django.contrib import admin

from .models import ChatMessage, CrisisEvent, UserChat


class ChannelOriginFilter(admin.SimpleListFilter):
    title = "канал"
    parameter_name = "origin"

    def lookups(self, request, model_admin):
        return (
            ("web", "Веб"),
            ("telegram", "Telegram"),
        )

    def queryset(self, request, queryset):
        if self.value() == "web":
            return queryset.filter(chat__user__channel_accounts__channel_type="web")
        if self.value() == "telegram":
            return queryset.filter(chat__user__channel_accounts__channel_type="telegram")
        return queryset


@admin.register(UserChat)
class UserChatAdmin(admin.ModelAdmin):
    list_display = ("user", "user_channels", "status", "model_version", "created_at", "updated_at")
    list_filter = ("status", ChannelOriginFilter)
    search_fields = (
        "user__email",
        "user__display_name",
        "user__channel_accounts__external_user_id",
        "user__channel_accounts__external_chat_id",
    )
    list_select_related = ("user", "model_version")

    @admin.display(description="Каналы")
    def user_channels(self, obj):
        return ", ".join(
            obj.user.channel_accounts.order_by("channel_type").values_list("channel_type", flat=True)
        )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("chat", "chat_user", "sender_role", "risk_score", "created_at")
    list_filter = ("sender_role", ChannelOriginFilter)
    search_fields = (
        "content_text",
        "chat__user__email",
        "chat__user__display_name",
        "chat__user__channel_accounts__external_user_id",
    )
    list_select_related = ("chat", "chat__user")

    @admin.display(description="Пользователь")
    def chat_user(self, obj):
        return obj.chat.user


@admin.register(CrisisEvent)
class CrisisEventAdmin(admin.ModelAdmin):
    list_display = ("chat", "risk_level", "screening_status", "status", "detected_at", "resolved_at")
    list_filter = ("risk_level", "screening_status", "status", ChannelOriginFilter)
    search_fields = (
        "chat__user__email",
        "chat__user__display_name",
        "trigger_message__content_text",
        "action_note",
    )
    list_select_related = ("chat", "chat__user", "trigger_message")
