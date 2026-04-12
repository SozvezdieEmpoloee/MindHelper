from django.contrib import admin

from .models import Appointment, EmergencyResource, Specialist, SpecialistLocation


@admin.register(EmergencyResource)
class EmergencyResourceAdmin(admin.ModelAdmin):
    list_display = ("service_name", "region_code", "contact_phone", "is_active")
    list_filter = ("region_code", "is_active")


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = ("full_name", "profession", "is_verified", "rating_avg")
    list_filter = ("profession", "is_verified")
    search_fields = ("full_name", "license_number")


@admin.register(SpecialistLocation)
class SpecialistLocationAdmin(admin.ModelAdmin):
    list_display = ("specialist", "city", "consultation_price", "is_active")
    list_filter = ("city", "is_active")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("user", "specialist", "status", "start_at", "end_at")
    list_filter = ("status",)

