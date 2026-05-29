"""Emails transaccionales del flujo de paciente."""
from django.conf import settings

from shared.emails import send_branded_email

from .models import PatientActivationToken


def send_activation_email(activation: PatientActivationToken) -> None:
    """
    Envía el correo de activación. Dos enlaces:

    1. Enlace **web** (`{SITE_URL}/rest/v1/public/patients/activate/?token=...`)
       — funciona en CUALQUIER dispositivo. Al abrirlo, el backend activa la
       cuenta y muestra una página HTML "Cuenta activada ✓".
    2. Enlace **deep-link** (`agendamiento://activate?token=...`) — opcional,
       para usuarios que ya tienen la app instalada y prefieren activarse desde
       ahí.

    Usa el template base compartido de marca NexoSoftDev.
    """
    user = activation.user
    web_link = f'{settings.SITE_URL.rstrip("/")}/rest/v1/public/patients/activate/?token={activation.token}'
    deep_link = f'agendamiento://activate?token={activation.token}'
    first_name = (user.first_name or '').strip() or user.email

    send_branded_email(
        subject='Activa tu cuenta de NexoSoftDev',
        to=user.email,
        template_name='patients/activate_email.html',
        text_template='patients/activate_email.txt',
        context={
            'first_name': first_name,
            'web_link': web_link,
            'deep_link': deep_link,
        },
    )
