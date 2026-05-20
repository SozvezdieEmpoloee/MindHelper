from django.db.models import Prefetch

from .models import EmergencyResource, Specialist, SpecialistLocation


def get_active_specialists():
    return Specialist.objects.filter(locations__is_active=True).distinct().prefetch_related(
        Prefetch("locations", queryset=SpecialistLocation.objects.filter(is_active=True))
    )


def get_active_emergency_resources():
    return EmergencyResource.objects.filter(is_active=True)
