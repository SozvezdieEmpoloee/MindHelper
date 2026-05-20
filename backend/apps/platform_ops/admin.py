from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .forms import OllamaAdminControlForm
from .models import ModerationCase, NeuralModelVersion, SiteContent
from .services import (
    OllamaServiceError,
    activate_model_version,
    ollama_list_models,
    ollama_pull_model,
    upsert_and_activate_model_version,
)


@admin.register(NeuralModelVersion)
class NeuralModelVersionAdmin(admin.ModelAdmin):
    list_display = ("version_tag", "model_name", "provider", "safety_profile", "is_active", "deployed_at")
    list_filter = ("is_active", "provider", "safety_profile")
    search_fields = ("version_tag", "model_name", "provider")
    actions = ("make_selected_version_active",)
    change_list_template = "admin/platform_ops/neuralmodelversion/change_list.html"

    def _get_ollama_form_initial(self) -> dict:
        return {
            "ollama_model_name": getattr(settings, "LLM_OLLAMA_MODEL", "qwen3:8b"),
            "version_tag": getattr(settings, "LLM_MODEL_VERSION_TAG", "ollama-qwen3-8b-local"),
            "model_name": getattr(settings, "LLM_MODEL_DISPLAY_NAME", "Qwen3-8B"),
            "provider": getattr(settings, "LLM_PROVIDER_LABEL", "ollama-local"),
            "safety_profile": getattr(settings, "LLM_SAFETY_PROFILE", "strict-v2"),
            "pull_before_activate": True,
        }

    @admin.action(description="Make selected version active")
    def make_selected_version_active(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                "Select exactly one model version to activate.",
                level=messages.ERROR,
            )
            return

        model_version = queryset.first()
        activate_model_version(model_version=model_version)
        self.message_user(request, f"Active model version set to: {model_version.version_tag}")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "ollama-control/",
                self.admin_site.admin_view(self.ollama_control_view),
                name="platform_ops_neuralmodelversion_ollama_control",
            ),
        ]
        return custom_urls + urls

    def ollama_control_view(self, request):
        form = OllamaAdminControlForm(initial=self._get_ollama_form_initial())
        if request.method == "POST":
            form = OllamaAdminControlForm(request.POST)
            if form.is_valid():
                cleaned = form.cleaned_data
                try:
                    if cleaned["pull_before_activate"]:
                        ollama_pull_model(model_name=cleaned["ollama_model_name"])
                    model_version, created = upsert_and_activate_model_version(
                        version_tag=cleaned["version_tag"],
                        model_name=cleaned["model_name"],
                        provider=cleaned["provider"],
                        safety_profile=cleaned["safety_profile"],
                        admin_user=request.user,
                    )
                    action = "created" if created else "updated"
                    self.message_user(
                        request,
                        f"Model version {action} and activated: {model_version.version_tag}",
                    )
                    changelist_url = reverse("admin:platform_ops_neuralmodelversion_changelist")
                    return redirect(changelist_url)
                except (OllamaServiceError, ValueError) as exc:
                    self.message_user(request, f"Ollama operation failed: {exc}", level=messages.ERROR)

        ollama_models = []
        ollama_error = ""
        try:
            ollama_models = ollama_list_models()
        except OllamaServiceError as exc:
            ollama_error = str(exc)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Ollama Control",
            "form": form,
            "ollama_models": ollama_models,
            "ollama_error": ollama_error,
            "changelist_url": reverse("admin:platform_ops_neuralmodelversion_changelist"),
        }
        return render(request, "admin/platform_ops/neuralmodelversion/ollama_control.html", context)


@admin.register(ModerationCase)
class ModerationCaseAdmin(admin.ModelAdmin):
    list_display = ("chat", "status", "opened_by_admin_user", "opened_at", "closed_at")
    list_filter = ("status",)
    search_fields = ("chat__user__email", "reason")


@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
    list_display = ("content_type", "slug", "title", "is_published", "updated_at")
    list_filter = ("content_type", "is_published")
    search_fields = ("slug", "title")
