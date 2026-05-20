import json
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import NeuralModelVersion


class OllamaServiceError(RuntimeError):
    pass


def _ollama_base_url() -> str:
    return getattr(settings, "LLM_OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")


def _ollama_timeout_seconds() -> float:
    return float(getattr(settings, "LLM_OLLAMA_TIMEOUT_SECONDS", 120))


def _ollama_request(*, path: str, method: str = "GET", payload: dict | None = None, timeout: float | None = None):
    url = f"{_ollama_base_url()}{path}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib_request.Request(url=url, data=data, method=method, headers=headers)
    request_timeout = _ollama_timeout_seconds() if timeout is None else timeout

    try:
        with urllib_request.urlopen(request, timeout=request_timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except (urllib_error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        raise OllamaServiceError(str(exc)) from exc


def ollama_list_models() -> list[dict]:
    payload = _ollama_request(path="/api/tags", method="GET")
    models = payload.get("models") or []
    if not isinstance(models, list):
        return []
    return [item for item in models if isinstance(item, dict)]


def ollama_pull_model(*, model_name: str, timeout_seconds: float = 900) -> dict:
    return _ollama_request(
        path="/api/pull",
        method="POST",
        payload={"name": model_name, "stream": False},
        timeout=timeout_seconds,
    )


def resolve_admin_user(*, admin_email: str):
    user_model = get_user_model()
    admin_user = user_model.objects.filter(email=admin_email).first()
    if admin_user:
        return admin_user

    admin_user = user_model.objects.filter(is_superuser=True).order_by("created_at").first()
    if admin_user:
        return admin_user

    admin_user = user_model.objects.filter(is_staff=True).order_by("created_at").first()
    if admin_user:
        return admin_user

    raise ValueError("No admin user found.")


@transaction.atomic
def activate_model_version(*, model_version: NeuralModelVersion) -> NeuralModelVersion:
    NeuralModelVersion.objects.exclude(id=model_version.id).filter(is_active=True).update(is_active=False)
    model_version.is_active = True
    if model_version.deployed_at is None:
        model_version.deployed_at = timezone.now()
    model_version.save(update_fields=("is_active", "deployed_at"))
    return model_version


@transaction.atomic
def upsert_and_activate_model_version(
    *,
    version_tag: str,
    model_name: str,
    provider: str,
    safety_profile: str,
    admin_user,
) -> tuple[NeuralModelVersion, bool]:
    model_version, created = NeuralModelVersion.objects.update_or_create(
        version_tag=version_tag,
        defaults={
            "model_name": model_name,
            "provider": provider,
            "safety_profile": safety_profile,
            "is_active": True,
            "deployed_at": timezone.now(),
            "created_by_admin_user": admin_user,
        },
    )
    activate_model_version(model_version=model_version)
    return model_version, created
