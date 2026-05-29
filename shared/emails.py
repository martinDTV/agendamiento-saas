"""
Utilidades compartidas para envío de correos transaccionales.

Mantiene la consistencia entre todos los correos del SaaS:
  - Mismo template base (shared/templates/email/_base.html)
  - Multipart (HTML + texto plano)
  - Formato de fechas/horas en español
  - Manejo silencioso de errores SMTP (los correos no son críticos para que
    el flujo principal funcione; si SMTP cae, el usuario puede reenviar)
"""
from datetime import date, time
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


# ── Formato de fechas en español ─────────────────────────────────────────────

_WEEKDAYS_ES = [
    'lunes', 'martes', 'miércoles', 'jueves',
    'viernes', 'sábado', 'domingo',
]
_MONTHS_ES = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]


def format_long_date_es(d: date) -> str:
    """`date(2026, 5, 29)` → 'Viernes 29 de mayo, 2026'."""
    weekday = _WEEKDAYS_ES[d.weekday()].capitalize()
    month = _MONTHS_ES[d.month - 1]
    return f'{weekday} {d.day} de {month}, {d.year}'


def format_time_12h_es(t: time) -> str:
    """`time(14, 30)` → '2:30 p. m.'"""
    hour = t.hour
    minute = t.minute
    period = 'p. m.' if hour >= 12 else 'a. m.'
    h12 = hour % 12 or 12
    return f'{h12}:{minute:02d} {period}'


# ── Envío de correos ─────────────────────────────────────────────────────────

def send_branded_email(
    *,
    subject: str,
    to: list[str] | str,
    template_name: str,
    context: dict,
    text_template: Optional[str] = None,
    from_email: Optional[str] = None,
    reply_to: Optional[list[str]] = None,
) -> bool:
    """
    Manda un correo HTML con el template base de NexoSoftDev.

    Args:
        subject: asunto del correo
        to: destinatario(s) — string o lista
        template_name: ej. 'patients/email/activate.html'
        context: variables para el template
        text_template: opcional, plantilla de texto plano. Si no se da, se
                       genera uno mínimo automáticamente (recomendado pasarlo
                       para mejor UX en clientes sin HTML).
        from_email: por defecto settings.DEFAULT_FROM_EMAIL
        reply_to: opcional, ej. ['soporte@nexosoftdev.com']

    Returns:
        True si el correo se envió sin lanzar excepción, False si falló.
        Nunca propaga la excepción (fail_silently style).
    """
    if isinstance(to, str):
        to = [to]

    html_body = render_to_string(template_name, context)
    if text_template:
        text_body = render_to_string(text_template, context)
    else:
        # Fallback mínimo: stripear tags HTML manualmente del HTML renderizado.
        # No es ideal pero evita que pongan plain=None.
        from django.utils.html import strip_tags
        text_body = strip_tags(html_body)

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            to=to,
            reply_to=reply_to,
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        return True
    except Exception:
        # No queremos que un fallo de SMTP rompa el endpoint principal.
        # Loguear sin crashear.
        import logging
        logging.getLogger(__name__).exception('Error enviando correo a %s', to)
        return False


def build_app_link(path: str) -> str:
    """
    Construye un link absoluto al SITE_URL del backend.
    `path` puede empezar o no con '/'.
    """
    site = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    if not path.startswith('/'):
        path = '/' + path
    return f'{site}{path}'
