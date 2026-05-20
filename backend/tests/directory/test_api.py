import pytest
from rest_framework.test import APIClient

from apps.directory.models import EmergencyResource, Specialist, SpecialistLocation


pytestmark = pytest.mark.django_db


def test_specialists_endpoint_is_public():
    specialist = Specialist.objects.create(
        full_name="Тестовый психолог",
        profession=Specialist.Profession.PSYCHOLOGIST,
        is_verified=True,
    )
    SpecialistLocation.objects.create(
        specialist=specialist,
        address_line="ул. Пушкина, 1, Воронеж",
        city="Воронеж",
        latitude=51.660800,
        longitude=39.200300,
        consultation_price=2500,
        currency="RUB",
        is_active=True,
    )

    response = APIClient().get("/api/v1/directory/specialists/")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["full_name"] == "Тестовый психолог"


def test_emergency_resources_endpoint_is_public():
    EmergencyResource.objects.create(
        region_code="RU",
        service_name="Тестовая линия",
        contact_phone="8 (800) 100-10-10",
        is_active=True,
    )

    response = APIClient().get("/api/v1/directory/emergency-resources/")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["service_name"] == "Тестовая линия"
