from rest_framework import serializers

from .models import ModerationCase, NeuralModelVersion, SiteContent


class NeuralModelVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NeuralModelVersion
        fields = (
            "id",
            "version_tag",
            "model_name",
            "provider",
            "safety_profile",
            "is_active",
            "deployed_at",
            "created_by_admin_user",
        )
        read_only_fields = ("id", "deployed_at", "created_by_admin_user")


class ModerationCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationCase
        fields = (
            "id",
            "chat",
            "message",
            "reason",
            "status",
            "opened_by_admin_user",
            "opened_at",
            "closed_at",
        )
        read_only_fields = ("id", "opened_by_admin_user", "opened_at")


class SiteContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteContent
        fields = (
            "id",
            "content_type",
            "slug",
            "title",
            "body",
            "is_published",
            "updated_by_admin_user",
            "updated_at",
        )
        read_only_fields = ("id", "updated_by_admin_user", "updated_at")

