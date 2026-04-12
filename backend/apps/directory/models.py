import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class EmergencyResource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    region_code = models.CharField(max_length=16)
    service_name = models.CharField(max_length=255)
    contact_phone = models.CharField(max_length=64, blank=True)
    contact_url = models.URLField(max_length=512, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "emergency_resource"
        ordering = ("service_name",)


class Specialist(models.Model):
    class Profession(models.TextChoices):
        PSYCHOLOGIST = "psychologist", "Psychologist"
        PSYCHIATRIST = "psychiatrist", "Psychiatrist"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    profession = models.CharField(max_length=32, choices=Profession.choices)
    license_number = models.CharField(max_length=64, blank=True)
    is_verified = models.BooleanField(default=False)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = "specialist"
        ordering = ("full_name",)


class SpecialistLocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    specialist = models.ForeignKey(
        Specialist,
        on_delete=models.CASCADE,
        related_name="locations",
    )
    address_line = models.CharField(max_length=512)
    city = models.CharField(max_length=120)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    consultation_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default="RUB")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "specialist_location"
        ordering = ("city", "address_line")


class Appointment(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    specialist = models.ForeignKey(
        Specialist,
        on_delete=models.RESTRICT,
        related_name="appointments",
    )
    location = models.ForeignKey(
        SpecialistLocation,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="appointments",
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=32, choices=Status.choices)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "appointment"
        ordering = ("start_at",)

