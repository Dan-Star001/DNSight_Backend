"""
Patients — Django ORM Models
==============================
Patient demographics with auto-generated PAT-XXXXX IDs scoped per hospital.
"""

from django.conf import settings
from django.db import models
import uuid



class Patient(models.Model):
    """Represents a patient record scoped to a hospital. The primary key is an
    auto-generated string in the format ``PAT-XXXXX``."""

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    ]

    id = models.CharField(max_length=50, primary_key=True, editable=False)
    hospital = models.ForeignKey(
        'hospitals.Hospital',
        on_delete=models.CASCADE,
        related_name='patients',
    )
    primary_doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patients',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    contact_info = models.JSONField(default=dict, blank=True)
    medical_history = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.id} — {self.first_name} {self.last_name}'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f'PAT-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)
