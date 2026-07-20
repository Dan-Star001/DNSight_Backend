"""
Appointments — DRF Serializers
=================================
Full CRUD serializer for appointment scheduling.
"""

from rest_framework import serializers

from appointments.models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    """Full CRUD serializer for appointments."""

    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'date', 'time', 'type', 'status',
        ]
        read_only_fields = ['id']

    def get_patient_name(self, obj) -> str | None:
        if obj.patient:
            return f'{obj.patient.first_name} {obj.patient.last_name}'
        return None

    def get_doctor_name(self, obj) -> str | None:
        if obj.doctor:
            return f'{obj.doctor.first_name} {obj.doctor.last_name}'
        return None
