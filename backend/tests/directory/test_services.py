from datetime import timedelta

import pytest
from django.utils import timezone

from apps.directory.models import Specialist, SpecialistLocation
from apps.directory.services import create_appointment


pytestmark = pytest.mark.django_db


def test_create_appointment_rejects_location_from_another_specialist(regular_user):
    first_specialist = Specialist.objects.create(
        full_name="Первый специалист",
        profession=Specialist.Profession.PSYCHOLOGIST,
        is_verified=True,
    )
    second_specialist = Specialist.objects.create(
        full_name="Второй специалист",
        profession=Specialist.Profession.PSYCHOLOGIST,
        is_verified=True,
    )
    foreign_location = SpecialistLocation.objects.create(
        specialist=second_specialist,
        address_line="ул. Тестовая, 1",
        city="Воронеж",
        latitude=51.661,
        longitude=39.200,
        consultation_price=2500,
        currency="RUB",
        is_active=True,
    )

    with pytest.raises(ValueError, match="Selected location does not belong to the chosen specialist."):
        create_appointment(
            user=regular_user,
            specialist=first_specialist,
            location=foreign_location,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(hours=1),
        )
