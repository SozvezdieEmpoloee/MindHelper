from django.db import transaction

from .models import Appointment


@transaction.atomic
def create_appointment(*, user, specialist, location, start_at, end_at) -> Appointment:
    if location and location.specialist_id != specialist.id:
        raise ValueError("Selected location does not belong to the chosen specialist.")

    return Appointment.objects.create(
        user=user,
        specialist=specialist,
        location=location,
        start_at=start_at,
        end_at=end_at,
        status=Appointment.Status.REQUESTED,
    )

