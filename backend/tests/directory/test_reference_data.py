import pytest
from django.core.management import call_command

from apps.directory.models import EmergencyResource, SpecialistLocation
from apps.directory.services import sync_reference_directory_data


pytestmark = pytest.mark.django_db


def test_sync_reference_directory_data_creates_expected_records():
    summary = sync_reference_directory_data()

    assert summary == {
        "emergency_resources": 2,
        "specialists": 4,
        "locations": 4,
    }
    assert EmergencyResource.objects.filter(service_name__icontains="МЧС").exists()
    assert SpecialistLocation.objects.filter(city="Воронеж").count() >= 4


def test_sync_reference_directory_command_is_idempotent():
    call_command("sync_directory_reference_data")
    call_command("sync_directory_reference_data")

    assert EmergencyResource.objects.count() == 2
    assert SpecialistLocation.objects.count() == 4
