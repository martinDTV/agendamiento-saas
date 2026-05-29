"""Correos transaccionales del flujo de citas (confirmación + recordatorio).

Usa el template HTML compartido de marca NexoSoftDev (shared/templates/email/).
Cada función arma el contexto con datos legibles del appointment, dispara el
correo multipart (HTML + texto), y NO propaga errores SMTP.
"""
from shared.emails import (
    build_app_link,
    format_long_date_es,
    format_time_12h_es,
    send_branded_email,
)


def _common_context(appointment) -> dict:
    """Context base reusado por confirmación y recordatorio."""
    patient_first_name = (appointment.patient_name or '').split(' ')[0] or 'Hola'

    # Branch puede ser nulo (catálogo flexible). El doctor puede tener branch
    # asignado o no.
    branch_name = ''
    branch_address = ''
    branch = getattr(appointment.doctor, 'branch', None)
    if branch:
        branch_name = branch.name or ''
        branch_address = getattr(branch, 'address', '') or ''

    return {
        'appointment': appointment,
        'patient_first_name': patient_first_name,
        'date_formatted': format_long_date_es(appointment.date),
        'date_formatted_short': appointment.date.strftime('%d/%m/%Y'),
        'time_formatted': format_time_12h_es(appointment.start_time),
        'branch_name': branch_name,
        'branch_address': branch_address,
        # Link a "mis citas" en la app móvil (deep-link).
        # En el futuro: cuando el sitio público tenga vista de cita, usar
        # un link http real.
        'cta_url': build_app_link('/'),
    }


def send_appointment_confirmation(appointment):
    """Correo enviado inmediatamente después de crear una cita."""
    ctx = _common_context(appointment)
    send_branded_email(
        subject=f'Cita confirmada — {appointment.tenant.name}',
        to=appointment.patient_email,
        template_name='notifications/email/confirmation.html',
        text_template='notifications/email/confirmation.txt',
        context=ctx,
    )


def send_appointment_reminder(appointment):
    """Correo enviado 24h antes de la cita."""
    ctx = _common_context(appointment)
    send_branded_email(
        subject=f'Recordatorio: tu cita es mañana — {appointment.tenant.name}',
        to=appointment.patient_email,
        template_name='notifications/email/reminder.html',
        text_template='notifications/email/reminder.txt',
        context=ctx,
    )
