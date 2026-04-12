from django.contrib import admin

from .models import ModerationCase, NeuralModelVersion, SiteContent


@admin.register(NeuralModelVersion)
class NeuralModelVersionAdmin(admin.ModelAdmin):
    list_display = ("version_tag", "model_name", "provider", "safety_profile", "is_active", "deployed_at")
    list_filter = ("is_active", "provider", "safety_profile")


@admin.register(ModerationCase)
class ModerationCaseAdmin(admin.ModelAdmin):
    list_display = ("chat", "status", "opened_by_admin_user", "opened_at", "closed_at")
    list_filter = ("status",)


@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
    list_display = ("content_type", "slug", "title", "is_published", "updated_at")
    list_filter = ("content_type", "is_published")
    search_fields = ("slug", "title")

