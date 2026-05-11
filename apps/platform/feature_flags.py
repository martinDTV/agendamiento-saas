"""
Feature flag schema y helpers para gating por plan.

Cada Plan tiene un dict `flags` que activa/desactiva features. El helper
`tenant_has_feature(tenant, key)` resuelve el flag del plan suscrito.

Si una feature está pendiente de implementación, se mantiene en DEFAULT_FLAGS
pero el endpoint la devuelve 402 hasta que la implementemos. Eso permite que
el plan ya prometa la feature aunque la pongamos en producción después.
"""

from functools import wraps

from rest_framework import status
from rest_framework.exceptions import APIException


# Schema canónico — cualquier flag nuevo se define aquí primero.
DEFAULT_FLAGS: dict[str, bool] = {
    # Comunicaciones
    'email_reminders': True,
    'sms_reminders': False,
    'whatsapp_reminders': False,

    # IA (Ollama local)
    'ai_booking_suggestions': False,    # sugerir servicios al paciente al reservar
    'ai_consult_summary': False,        # resumir motivo de consulta
    'ai_marketing_copy': False,         # generar textos del CMS

    # Análisis
    'reports_basic': False,
    'reports_advanced': False,

    # Personalización
    'cms_editor': False,                # editor de contenido del sitio público
    'white_label': False,               # ocultar "Powered by"
    'custom_domain': False,             # dominio propio

    # Integraciones
    'api_access': False,                # generar API key
    'outbound_webhooks': False,         # webhooks salientes
    'sso_saml': False,                  # SSO empresarial

    # Soporte
    'priority_support': False,
    'dedicated_sla': False,
    'chat_human_support': False,        # burbuja de chat con agente humano (Starter+)
    'chat_ai_support': False,           # asistente IA en chat (Pro+)
}


def merged_flags(plan_flags: dict | None) -> dict[str, bool]:
    """Mezcla flags del plan con defaults, ignorando keys desconocidas."""
    out = dict(DEFAULT_FLAGS)
    for k, v in (plan_flags or {}).items():
        if k in DEFAULT_FLAGS:
            out[k] = bool(v)
    return out


def tenant_has_feature(tenant, key: str) -> bool:
    """
    True si el tenant tiene activa la feature `key` en su plan suscrito.
    Lookup: tenant → Subscription.plan.flags[key].
    Si no hay suscripción o el flag no existe, retorna False.
    """
    if key not in DEFAULT_FLAGS:
        return False
    sub = getattr(tenant, 'subscription', None)
    if sub is None or not sub.plan:
        return False
    return bool(sub.plan.flags.get(key, False))


# ── DRF helpers ───────────────────────────────────────────────────────────────


class FeatureNotInPlan(APIException):
    """402 Payment Required — feature no disponible en el plan actual."""
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = 'Esta funcionalidad no está incluida en tu plan.'
    default_code = 'feature_not_in_plan'


def requires_feature(flag_key: str, upgrade_message: str | None = None):
    """
    Decorator para vistas DRF: lanza FeatureNotInPlan (402) si el tenant
    del request no tiene la feature activada.

    Asume que `request.tenant` está poblado por el middleware multi-tenant.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(self_or_request, *args, **kwargs):
            request = self_or_request if hasattr(self_or_request, 'tenant') else args[0]
            tenant = getattr(request, 'tenant', None)
            if tenant is None or not tenant_has_feature(tenant, flag_key):
                msg = upgrade_message or (
                    f'La función "{flag_key}" no está incluida en tu plan. '
                    'Actualiza tu suscripción para acceder.'
                )
                raise FeatureNotInPlan(msg)
            return view_func(self_or_request, *args, **kwargs)
        return wrapped
    return decorator
