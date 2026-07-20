"""
Appointments — DRF Views
===========================
Full CRUD for appointment scheduling, filtered by tenant hospital.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend

from analytics.mixins import log_action
from appointments.models import Appointment
from appointments.serializers import AppointmentSerializer
from users.permissions import IsActiveUser


class AppointmentViewSet(viewsets.ModelViewSet):
    """Full CRUD for appointments, filtered by the current doctor's hospital."""

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsActiveUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'date', 'patient']

    def get_queryset(self):
        """Tenant-scoped queryset."""
        return (
            Appointment.objects
            .filter(doctor__hospital_id=self.request.user.hospital_id)
            .select_related('patient', 'doctor')
            .only(
                'id', 'date', 'time', 'type', 'status',
                'patient__id', 'patient__first_name', 'patient__last_name',
                'doctor__id', 'doctor__first_name', 'doctor__last_name',
            )
        )

    def perform_create(self, serializer):
        appointment = serializer.save()
        log_action(
            self.request,
            action='Scheduled appointment',
            details={
                'appointment_id': appointment.id,
                'patient_id': str(appointment.patient_id),
                'date': str(appointment.date),
            },
        )

        from appointments.tasks import send_appointment_email
        send_appointment_email.delay(appointment.id)
