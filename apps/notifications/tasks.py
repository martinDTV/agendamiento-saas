from celery import shared_task
from datetime import date, timedelta


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def task_send_confirmation(self, appointment_id: int):
    from apps.bookings.models import Appointment
    from .emails import send_appointment_confirmation
    try:
        appt = Appointment._all.select_related('tenant', 'doctor__user', 'service').get(pk=appointment_id)
        send_appointment_confirmation(appt)
    except Appointment.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def task_send_reminders():
    """Send 24-hour reminders for tomorrow's pending/confirmed appointments."""
    from apps.bookings.models import Appointment, AppointmentStatus
    from .emails import send_appointment_reminder

    tomorrow = date.today() + timedelta(days=1)
    appointments = (
        Appointment._all
        .select_related('tenant', 'doctor__user', 'service')
        .filter(date=tomorrow, status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
    )
    for appt in appointments:
        send_appointment_reminder(appt)
