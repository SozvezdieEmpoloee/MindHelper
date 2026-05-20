from django.db import transaction

from .models import Appointment, EmergencyResource, Specialist, SpecialistLocation


REFERENCE_EMERGENCY_RESOURCES = (
    {
        "id": "a4c8dc31-8ea0-4d74-8a3a-b4174c581001",
        "region_code": "RU",
        "service_name": "Горячая линия психологической помощи МЧС России",
        "contact_phone": "8 (499) 216-50-50",
        "contact_url": "",
        "is_active": True,
    },
    {
        "id": "a4c8dc31-8ea0-4d74-8a3a-b4174c581002",
        "region_code": "RU",
        "service_name": "Бесплатная кризисная линия доверия по России",
        "contact_phone": "8 (800) 333-44-34",
        "contact_url": "",
        "is_active": True,
    },
)

REFERENCE_SPECIALISTS = (
    {
        "specialist": {
            "id": "a4c8dc31-8ea0-4d74-8a3a-b4174c582001",
            "full_name": "Воронежский областной клинический психоневрологический диспансер",
            "profession": Specialist.Profession.PSYCHIATRIST,
            "license_number": "",
            "is_verified": True,
            "rating_avg": None,
        },
        "location": {
            "id": "a4c8dc31-8ea0-4d74-8a3a-b4174c583001",
            "address_line": "ул. 20-летия Октября, 73, Воронеж",
            "city": "Воронеж",
            "latitude": 51.649327,
            "longitude": 39.188411,
            "consultation_price": None,
            "currency": "RUB",
            "is_active": True,
        },
    },
    {
        "specialist": {
            "id": "a4c8dc31-8ea0-4d74-8a3a-b4174c582002",
            "full_name": "Медико-психологический центр «Modus-Vivendi»",
            "profession": Specialist.Profession.PSYCHIATRIST,
            "license_number": "",
            "is_verified": True,
            "rating_avg": None,
        },
        "location": {
            "id": "a4c8dc31-8ea0-4d74-8a3a-b4174c583002",
            "address_line": "ул. Кирова, 9, офис 28, Воронеж",
            "city": "Воронеж",
            "latitude": 51.656585,
            "longitude": 39.189732,
            "consultation_price": 3500.00,
            "currency": "RUB",
            "is_active": True,
        },
    },
    {
        "specialist": {
            "id": "a4c8dc31-8ea0-4d74-8a3a-b4174c582003",
            "full_name": "Психологический центр «Первый шаг»",
            "profession": Specialist.Profession.PSYCHOLOGIST,
            "license_number": "",
            "is_verified": True,
            "rating_avg": None,
        },
        "location": {
            "id": "a4c8dc31-8ea0-4d74-8a3a-b4174c583003",
            "address_line": "ул. Владимира Невского, 38Е, Воронеж",
            "city": "Воронеж",
            "latitude": 51.710835,
            "longitude": 39.154877,
            "consultation_price": 3000.00,
            "currency": "RUB",
            "is_active": True,
        },
    },
    {
        "specialist": {
            "id": "a4c8dc31-8ea0-4d74-8a3a-b4174c582004",
            "full_name": "Психологический центр «Персона»",
            "profession": Specialist.Profession.PSYCHOLOGIST,
            "license_number": "",
            "is_verified": True,
            "rating_avg": None,
        },
        "location": {
            "id": "a4c8dc31-8ea0-4d74-8a3a-b4174c583004",
            "address_line": "ул. Кирова, 9, офис 12, Воронеж",
            "city": "Воронеж",
            "latitude": 51.656585,
            "longitude": 39.189732,
            "consultation_price": 3200.00,
            "currency": "RUB",
            "is_active": True,
        },
    },
)


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


@transaction.atomic
def sync_reference_directory_data() -> dict[str, int]:
    emergency_count = 0
    specialist_count = 0
    location_count = 0

    for resource in REFERENCE_EMERGENCY_RESOURCES:
        EmergencyResource.objects.update_or_create(
            id=resource["id"],
            defaults={
                "region_code": resource["region_code"],
                "service_name": resource["service_name"],
                "contact_phone": resource["contact_phone"],
                "contact_url": resource["contact_url"],
                "is_active": resource["is_active"],
            },
        )
        emergency_count += 1

    for item in REFERENCE_SPECIALISTS:
        specialist_data = item["specialist"]
        location_data = item["location"]

        specialist, _ = Specialist.objects.update_or_create(
            id=specialist_data["id"],
            defaults={
                "full_name": specialist_data["full_name"],
                "profession": specialist_data["profession"],
                "license_number": specialist_data["license_number"],
                "is_verified": specialist_data["is_verified"],
                "rating_avg": specialist_data["rating_avg"],
            },
        )
        specialist_count += 1

        SpecialistLocation.objects.update_or_create(
            id=location_data["id"],
            defaults={
                "specialist": specialist,
                "address_line": location_data["address_line"],
                "city": location_data["city"],
                "latitude": location_data["latitude"],
                "longitude": location_data["longitude"],
                "consultation_price": location_data["consultation_price"],
                "currency": location_data["currency"],
                "is_active": location_data["is_active"],
            },
        )
        location_count += 1

    return {
        "emergency_resources": emergency_count,
        "specialists": specialist_count,
        "locations": location_count,
    }
