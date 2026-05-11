from django.core.mail import send_mail
from django.conf import settings


def send_appointment_confirmation(appointment):
    tenant_name = appointment.tenant.name
    doctor_name = str(appointment.doctor)
    service_name = appointment.service.name
    date_str = appointment.date.strftime('%d/%m/%Y')
    time_str = appointment.start_time.strftime('%H:%M')

    subject = f'Confirmación de cita — {tenant_name}'
    body = (
        f'Hola {appointment.patient_name},\n\n'
        f'Tu cita ha sido agendada exitosamente:\n\n'
        f'  Doctor:   {doctor_name}\n'
        f'  Servicio: {service_name}\n'
        f'  Fecha:    {date_str} a las {time_str}\n\n'
        f'Si necesitas cancelar o reagendar, contáctanos.\n\n'
        f'— {tenant_name}'
    )
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [appointment.patient_email], fail_silently=True)


def send_appointment_reminder(appointment):
    tenant_name = appointment.tenant.name
    doctor_name = str(appointment.doctor)
    date_str = appointment.date.strftime('%d/%m/%Y')
    time_str = appointment.start_time.strftime('%H:%M')

    subject = f'Recordatorio de cita mañana — {tenant_name}'
    body = (
        f'Hola {appointment.patient_name},\n\n'
        f'Te recordamos que tienes una cita mañana:\n\n'
        f'  Doctor: {doctor_name}\n'
        f'  Fecha:  {date_str} a las {time_str}\n\n'
        f'— {tenant_name}'
    )
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [appointment.patient_email], fail_silently=True)
