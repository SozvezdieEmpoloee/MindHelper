from rest_framework import serializers

from .models import UserAccount
from .selectors import build_user_dashboard_stats


class UserAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ("id", "email", "display_name", "status", "created_at")


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = UserAccount
        fields = ("email", "display_name", "password")

    def create(self, validated_data):
        password = validated_data.pop("password")
        return UserAccount.objects.create_user(password=password, **validated_data)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserDashboardStatsSerializer(serializers.Serializer):
    chat_id = serializers.UUIDField(allow_null=True)
    total_messages = serializers.IntegerField()
    last_message_at = serializers.DateTimeField(allow_null=True)
    assessment_sessions = serializers.IntegerField()
    last_assessment_completed_at = serializers.DateTimeField(allow_null=True)
    next_appointment = serializers.JSONField(allow_null=True)

    @classmethod
    def from_user(cls, user):
        return cls(build_user_dashboard_stats(user))
