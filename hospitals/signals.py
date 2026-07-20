from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.contrib.auth import get_user_model

from patients.models import Patient
from assessments.models import Assessment
from appointments.models import Appointment
from hospitals.views import CACHE_KEY_ADMIN_STATS

User = get_user_model()


def clear_hospital_cache(hospital_id):
    if hospital_id:
        cache.delete(CACHE_KEY_ADMIN_STATS.format(hospital_id=hospital_id))

def clear_doctor_cache(doctor_id):
    if doctor_id:
        cache.delete(f'doctor_stats_{doctor_id}')


@receiver([post_save, post_delete], sender=User)
def invalidate_user_cache(sender, instance, **kwargs):
    if instance.role == 'DOCTOR' and instance.hospital_id:
        clear_hospital_cache(instance.hospital_id)


@receiver([post_save, post_delete], sender=Patient)
def invalidate_patient_cache(sender, instance, **kwargs):
    if instance.hospital_id:
        clear_hospital_cache(instance.hospital_id)
    if instance.primary_doctor_id:
        clear_doctor_cache(instance.primary_doctor_id)


@receiver([post_save, post_delete], sender=Assessment)
def invalidate_assessment_cache(sender, instance, **kwargs):
    # Assessment's hospital is derived from patient
    if instance.patient and instance.patient.hospital_id:
        clear_hospital_cache(instance.patient.hospital_id)
    if instance.doctor_id:
        clear_doctor_cache(instance.doctor_id)


@receiver([post_save, post_delete], sender=Appointment)
def invalidate_appointment_cache(sender, instance, **kwargs):
    if instance.doctor and instance.doctor.hospital_id:
        clear_hospital_cache(instance.doctor.hospital_id)
    if instance.doctor_id:
        clear_doctor_cache(instance.doctor_id)
