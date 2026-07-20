from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_doctor_registration_email(self,email, name):

    try:
        """
        Send an email to a doctor after they register, informing them that their
        account is waiting for admin approval.
        """
        subject = 'Registration Pending Approval'
        message = (
            f'Hello Dr. {name},\n\n'
            'Thank you for registering with DNSight. Your account is currently pending '
            'approval from a hospital administrator. You will receive another email once '
            'your account status has been updated.\n\n'
            'Best regards,\nThe DNSight Team'
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    
    except Exception as exc:
        raise self.retry(exc=exc)




@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_doctor_status_email(self, email, name, status):


    try:
        """
        Send an email to a doctor when their account is approved or rejected.
        """
        if status == 'ACTIVE':
            subject = 'Account Approved'
            message = (
                f'Hello Dr. {name},\n\n'
                'Great news! Your DNSight account has been approved by an administrator. '
                'You can now log in and access your dashboard.\n\n'
                'Best regards,\nThe DNSight Team'
            )
        elif status == 'REJECTED':
            subject = 'Account Registration Update'
            message = (
                f'Hello Dr. {name},\n\n'
                'We regret to inform you that your DNSight account registration has '
                'been rejected. Please contact your hospital administrator for more details.\n\n'
                'Best regards,\nThe DNSight Team'
            )
        else:
            return

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
    except Exception as exc:
        raise self.retry(exc=exc)