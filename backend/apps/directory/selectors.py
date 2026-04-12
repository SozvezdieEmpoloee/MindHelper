from .models import EmergencyResource, Specialist


def get_active_specialists():
    return Specialist.objects.filter(locations__is_active=True).distinct().prefetch_related("locations")


def get_active_emergency_resources():
    return EmergencyResource.objects.filter(is_active=True)

