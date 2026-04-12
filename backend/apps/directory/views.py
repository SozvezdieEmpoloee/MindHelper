from rest_framework import generics, permissions

from .models import Appointment
from .selectors import get_active_emergency_resources, get_active_specialists
from .serializers import AppointmentSerializer, EmergencyResourceSerializer, SpecialistSerializer
from .services import create_appointment


class SpecialistListAPIView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SpecialistSerializer

    def get_queryset(self):
        return get_active_specialists()


class EmergencyResourceListAPIView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = EmergencyResourceSerializer

    def get_queryset(self):
        return get_active_emergency_resources()


class AppointmentListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        return Appointment.objects.filter(user=self.request.user).select_related("specialist", "location")

    def perform_create(self, serializer):
        specialist = serializer.validated_data["specialist"]
        location = serializer.validated_data.get("location")
        appointment = create_appointment(
            user=self.request.user,
            specialist=specialist,
            location=location,
            start_at=serializer.validated_data["start_at"],
            end_at=serializer.validated_data["end_at"],
        )
        serializer.instance = appointment

