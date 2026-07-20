"""Patients — Django Admin Configuration"""

from django.contrib import admin

from patients.models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'hospital', 'status', 'created_at')
    list_filter = ('status', 'hospital', 'gender')
    search_fields = ('id', 'first_name', 'last_name')
