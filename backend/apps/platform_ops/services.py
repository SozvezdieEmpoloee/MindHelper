from django.db import transaction
from django.utils import timezone

from .models import NeuralModelVersion


@transaction.atomic
def activate_model_version(*, model_version: NeuralModelVersion) -> NeuralModelVersion:
    NeuralModelVersion.objects.exclude(id=model_version.id).filter(is_active=True).update(is_active=False)
    model_version.is_active = True
    if model_version.deployed_at is None:
        model_version.deployed_at = timezone.now()
    model_version.save(update_fields=("is_active", "deployed_at"))
    return model_version

