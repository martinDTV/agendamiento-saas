"""Correos del flujo de leads: aviso interno + confirmación al prospecto."""
from django.conf import settings

from shared.emails import send_branded_email

# Etiquetas legibles de los planes para los correos.
PLAN_LABELS = {
    'gratuito': 'Gratuito',
    'free': 'Gratuito',
    'profesional': 'Profesional',
    'clinica': 'Clínica',
    'clinic': 'Clínica',
    'enterprise': 'Enterprise',
}


def _plan_label(plan: str) -> str:
    return PLAN_LABELS.get((plan or '').lower(), plan or 'No especificado')


def send_lead_notifications(lead) -> None:
    """
    Dispara los dos correos de un nuevo lead:
      1. Aviso interno al equipo (LEADS_NOTIFY_EMAIL).
      2. Confirmación al prospecto de que lo contactaremos.
    Ninguno propaga errores SMTP.
    """
    plan_label = _plan_label(lead.plan)

    # 1) Aviso interno
    notify_to = getattr(settings, 'LEADS_NOTIFY_EMAIL', None) or settings.DEFAULT_FROM_EMAIL
    send_branded_email(
        subject=f'Nuevo lead — {lead.name} ({plan_label})',
        to=notify_to,
        template_name='leads/email/internal.html',
        text_template='leads/email/internal.txt',
        context={'lead': lead, 'plan_label': plan_label},
        reply_to=[lead.email] if lead.email else None,
    )

    # 2) Confirmación al prospecto
    if lead.email:
        send_branded_email(
            subject='Recibimos tu solicitud — NexoSoftDev',
            to=lead.email,
            template_name='leads/email/confirmation.html',
            text_template='leads/email/confirmation.txt',
            context={
                'lead': lead,
                'plan_label': plan_label,
                'first_name': (lead.name or '').split(' ')[0] or 'Hola',
            },
        )
