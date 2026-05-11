from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Doctor, Service
from apps.platform.feature_flags import tenant_has_feature
from .ollama import chat_reply, suggest_booking


class ServiceSuggestView(APIView):
    """
    POST /rest/v1/public/ai/suggest/
    Body: { "reason": "..." }
    Returns:
        { "service_ids": ["uuid", ...], "doctor_ids": ["uuid", ...] }
        { "service_ids": [], "doctor_ids": [], "feature_gated": true }
            si el plan del tenant no tiene `ai_booking_suggestions`.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        reason = (request.data.get('reason') or '').strip()

        if not reason or not tenant:
            return Response({'service_ids': [], 'doctor_ids': []})

        # Gate por plan — si no tiene la feature, devuelve listas vacías + bandera.
        # No usamos 402 para no romper la experiencia del paciente; el front puede
        # ocultar el botón "Sugerir" si recibe feature_gated=True.
        if not tenant_has_feature(tenant, 'ai_booking_suggestions'):
            return Response({'service_ids': [], 'doctor_ids': [], 'feature_gated': True})

        services = list(
            Service.objects.for_tenant(tenant)
            .filter(is_active=True)
            .values('id', 'name', 'description')
        )
        services_payload = [
            {'id': str(s['id']), 'name': s['name'], 'description': s.get('description', '') or ''}
            for s in services
        ]

        doctors_qs = Doctor.objects.for_tenant(tenant).filter(is_active=True).select_related('user')
        doctors_payload = [
            {
                'id': str(d.id),
                'full_name': d.user.get_full_name() or d.user.email,
                'specialty': d.specialty or '',
            }
            for d in doctors_qs
        ]

        service_ids, doctor_ids = suggest_booking(reason, services_payload, doctors_payload)
        return Response({'service_ids': service_ids, 'doctor_ids': doctor_ids})


class ChatReplyView(APIView):
    """
    POST /rest/v1/public/ai/chat/
    Body: { "message": "...", "history": [{"role":"user|assistant", "content":"..."}] }

    Devuelve { "reply": "...", "should_escalate": bool } usando Ollama con
    contexto del tenant (servicios + doctores). Sólo disponible si el plan tiene
    `chat_ai_support`. Sino, devuelve `{ "feature_gated": true }`.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        message = (request.data.get('message') or '').strip()
        history = request.data.get('history') or []

        if not tenant or not message:
            return Response({'reply': '', 'should_escalate': False})

        if not tenant_has_feature(tenant, 'chat_ai_support'):
            return Response({'feature_gated': True, 'reply': '', 'should_escalate': False})

        services = list(
            Service.objects.for_tenant(tenant)
            .filter(is_active=True)
            .values('name', 'duration', 'price')
        )
        services_payload = [
            {'name': s['name'], 'duration': s['duration'], 'price': str(s['price'])}
            for s in services
        ]

        doctors_qs = Doctor.objects.for_tenant(tenant).filter(is_active=True).select_related('user')
        doctors_payload = [
            {
                'name': d.user.get_full_name() or d.user.email,
                'specialty': d.specialty or '',
            }
            for d in doctors_qs
        ]

        ctx = {
            'name': tenant.name,
            'services': services_payload,
            'doctors': doctors_payload,
        }

        reply = chat_reply(message, history if isinstance(history, list) else [], ctx)
        # Escalación heurística: si la IA menciona "agente humano" o el usuario lo pide
        triggers = ['agente humano', 'hablar con alguien', 'humano']
        should_escalate = any(t in reply.lower() for t in triggers) or any(t in message.lower() for t in triggers)
        return Response({'reply': reply, 'should_escalate': should_escalate})
