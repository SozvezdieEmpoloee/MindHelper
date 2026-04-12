from rest_framework import serializers

from .models import Appointment, EmergencyResource, Specialist, SpecialistLocation


class SpecialistLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialistLocation
        fields = (
            "id",
            "address_line",
            "city",
            "latitude",
            "longitude",
            "consultation_price",
            "currency",
            "is_active",
        )


class SpecialistSerializer(serializers.ModelSerializer):
    locations = SpecialistLocationSerializer(many=True, read_only=True)

    class Meta:
        model = Specialist
        fields = (
            "id",
            "full_name",
            "profession",
            "license_number",
            "is_verified",
            "rating_avg",
            "locations",
        )


class EmergencyResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyResource
        fields = ("id", "region_code", "service_name", "contact_phone", "contact_url", "is_active")


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = (
            "id",
            "user",
            "specialist",
            "location",
            "start_at",
            "end_at",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "user", "status", "created_at")

