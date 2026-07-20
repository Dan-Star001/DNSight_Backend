"""Appointments — Django Admin Configuration"""

from django.contrib import admin

from appointments.models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'date', 'time', 'type', 'status')
    list_filter = ('status', 'date')
    search_fields = ('patient__first_name', 'patient__last_name')
