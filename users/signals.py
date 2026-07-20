from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from users.tasks import send_doctor_status_email

User = get_user_model()


@receiver(pre_save, sender=User)
def capture_old_doctor_status(sender, instance, **kwargs):
    """
    Capture the old status before saving, to be used in post_save.
    """
    if not instance.pk:
        instance._old_status = None
        return

    try:
        old_instance = User.objects.get(pk=instance.pk)
        instance._old_status = old_instance.status
    except User.DoesNotExist:
        instance._old_status = None


@receiver(post_save, sender=User)
def notify_doctor_status_change(sender, instance, created, **kwargs):
    """
    Check if a doctor's status changed from PENDING to ACTIVE or REJECTED
    and trigger the appropriate email notification via Celery.
    """
    if created:
        return

    old_status = getattr(instance, '_old_status', None)

    # If the status has changed
    if instance.role == 'DOCTOR' and old_status is not None and old_status != instance.status and instance.status in ('ACTIVE', 'REJECTED'):
        transaction.on_commit(lambda: send_doctor_status_email.delay(
            instance.email,
            instance.first_name,
            instance.status
        ))
