from django import forms


class OllamaAdminControlForm(forms.Form):
    ollama_model_name = forms.CharField(
        max_length=120,
        label="Ollama model name",
        help_text="Example: qwen3:8b",
    )
    version_tag = forms.CharField(
        max_length=64,
        label="Version tag",
        help_text="Version key stored in neural_model_version.",
    )
    model_name = forms.CharField(
        max_length=120,
        label="Model display name",
    )
    provider = forms.CharField(
        max_length=120,
        label="Provider label",
    )
    safety_profile = forms.CharField(
        max_length=64,
        label="Safety profile",
    )
    pull_before_activate = forms.BooleanField(
        required=False,
        initial=True,
        label="Pull model before activation",
    )
