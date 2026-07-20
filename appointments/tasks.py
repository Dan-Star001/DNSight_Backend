from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from appointments.models import Appointment

@shared_task
def send_appointment_email(appointment_id):
    """
    Fetch an appointment by ID and send its details to the patient's email.
    """
    try:
        appointment = Appointment.objects.select_related('patient', 'doctor', 'doctor__hospital').get(id=appointment_id)
    except Appointment.DoesNotExist:
        return

    patient = appointment.patient
    if not patient.email:
        return

    doctor = appointment.doctor
    hospital = doctor.hospital

    # Format the date and time
    date_str = appointment.date.strftime("%B %d, %Y")
    time_str = appointment.time.strftime("%I:%M %p")    

    subject = f'Appointment Confirmation at {hospital.name}'
    message = (
        f'Hello {patient.first_name} {patient.last_name},\n\n'
        f'This email is to confirm your upcoming appointment at {hospital.name}.\n\n'
        f'Details:\n'
        f'- Doctor: Dr. {doctor.first_name} {doctor.last_name}\n'
        f'- Date: {date_str}\n'
        f'- Time: {time_str}\n'
        f'- Type: {appointment.type}\n\n'
        'Please ensure you arrive 10 minutes early. If you need to cancel or reschedule, '
        'please contact the hospital directly.\n\n'
        'Best regards,\n'
        f'The {hospital.name} Team'
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[patient.email],
        fail_silently=False,
    )
