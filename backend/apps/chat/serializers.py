from rest_framework import serializers

from .models import ChatMessage, CrisisEvent, UserChat


class UserChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserChat
        fields = ("id", "status", "model_version", "created_at", "updated_at")


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("id", "chat", "sender_role", "content_text", "risk_score", "created_at")
        read_only_fields = ("id", "chat", "sender_role", "risk_score", "created_at")


class ChatMessageCreateSerializer(serializers.Serializer):
    content_text = serializers.CharField()


class CrisisEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrisisEvent
        fields = (
            "id",
            "chat",
            "trigger_message",
            "emergency_resource",
            "risk_level",
            "status",
            "action_note",
            "detected_at",
            "resolved_at",
        )

