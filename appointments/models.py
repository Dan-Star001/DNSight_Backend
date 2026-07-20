"""
Appointments — Django ORM Models
==================================
Scheduled, completed, or cancelled visits between doctors and patients.
"""

from django.conf import settings
from django.db import models


class Appointment(models.Model):
    """Represents a scheduled, completed, or cancelled visit between a
    doctor and a patient."""

    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.BigAutoField(primary_key=True)
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='appointments',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments',
    )
    date = models.DateField()
    time = models.TimeField()
    type = models.CharField(
        max_length=100,
        help_text='E.g. "Risk Assessment", "Follow-up".',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED',
    )

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f'{self.type} — {self.patient_id} on {self.date}'
