from django.urls import path

from .views import AppointmentListCreateAPIView, EmergencyResourceListAPIView, SpecialistListAPIView


urlpatterns = [
    path("specialists/", SpecialistListAPIView.as_view(), name="directory-specialists"),
    path("emergency-resources/", EmergencyResourceListAPIView.as_view(), name="directory-resources"),
    path("appointments/", AppointmentListCreateAPIView.as_view(), name="directory-appointments"),
]
