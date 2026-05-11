"""
Endpoints PayPal para flujo de suscripciones.

Rutas (montadas en apps.platform.urls):
    POST /rest/v1/platform/paypal/sync-plans/        (super admin)
    POST /rest/v1/platform/paypal/subscribe/<slug>/  (tenant admin)
    GET  /rest/v1/platform/paypal/return/            (callback de PayPal después de aprobar)
    POST /rest/v1/platform/paypal/cancel/            (tenant admin)
    POST /rest/v1/platform/paypal/webhook/           (público, verifica firma)
"""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsTenantAdminOrOwner
from apps.platform.models import (
    PaymentEventType,
    PaymentTransaction,
    Plan,
    Subscription,
    SubscriptionStatus,
)
from apps.platform.permissions import IsPlatformAdmin

from .client import PayPalError, get_paypal_client


logger = logging.getLogger(__name__)


# ── Sync local Plans → PayPal Products + Billing Plans ────────────────────────


class PayPalSetProductIdsView(APIView):
    """
    PATCH /rest/v1/platform/paypal/set-product-ids/

    Body: { "starter": "PROD-XXX", "pro": "PROD-YYY", ... }

    Para cuentas sandbox donde /v1/catalog/products devuelve 404, el super admin
    crea los Products manualmente vía dashboard de PayPal y pega los IDs aquí.
    Después corre sync-plans (que skipea creación de Product si ya tiene ID).
    """
    permission_classes = [IsPlatformAdmin]

    def patch(self, request):
        updated = []
        for slug, product_id in request.data.items():
            if not isinstance(product_id, str):
                continue
            n = Plan.objects.filter(slug=slug).update(paypal_product_id=product_id.strip())
            if n:
                updated.append({'slug': slug, 'paypal_product_id': product_id.strip()})
        return Response({'updated': updated})


class PayPalSyncPlansView(APIView):
    """
    POST /rest/v1/platform/paypal/sync-plans/

    Para cada Plan local con price_monthly > 0 y is_active=True:
    1. Crea (si no existe) un Product en PayPal y guarda paypal_product_id.
    2. Crea (si no existe) un Billing Plan en PayPal y guarda paypal_plan_id.

    Idempotente: si un Plan ya tiene paypal_plan_id, lo salta. Para forzar
    re-creación (e.g. al cambiar precio), pasa { "force": true }.

    Solo super admin.
    """
    permission_classes = [IsPlatformAdmin]

    def post(self, request):
        force = bool(request.data.get('force'))
        results = []
        client = get_paypal_client()

        plans = Plan.objects.filter(is_active=True).exclude(price_monthly=0)
        for plan in plans:
            entry = {'slug': plan.slug, 'name': plan.name, 'price_monthly': str(plan.price_monthly)}
            try:
                if not plan.paypal_product_id or force:
                    product = client.create_product(
                        name=plan.name,
                        description=plan.description or plan.name,
                        request_id=f'product-{plan.slug}-{int(timezone.now().timestamp()) if force else "v1"}',
                    )
                    plan.paypal_product_id = product['id']

                if not plan.paypal_plan_id or force:
                    billing_plan = client.create_billing_plan(
                        product_id=plan.paypal_product_id,
                        name=plan.name,
                        price_monthly=float(plan.price_monthly),
                        currency=plan.currency or 'MXN',
                        description=plan.description or plan.name,
                        request_id=f'plan-{plan.slug}-{int(timezone.now().timestamp()) if force else "v1"}',
                    )
                    plan.paypal_plan_id = billing_plan['id']

                plan.save(update_fields=['paypal_product_id', 'paypal_plan_id', 'updated_at'])
                entry['paypal_product_id'] = plan.paypal_product_id
                entry['paypal_plan_id'] = plan.paypal_plan_id
                entry['ok'] = True
            except PayPalError as e:
                logger.exception('Error sincronizando plan %s con PayPal', plan.slug)
                entry['ok'] = False
                entry['error'] = str(e)
                entry['paypal_response'] = e.data
            results.append(entry)

        return Response({'results': results})


# ── Subscribe (tenant admin) ──────────────────────────────────────────────────


class PayPalSubscribeView(APIView):
    """
    POST /rest/v1/platform/paypal/subscribe/<slug>/

    Crea una subscription en PayPal y devuelve la URL de aprobación.
    El frontend redirige al usuario a esa URL. Después de aprobar, PayPal
    redirige a return_url con ?subscription_id=<paypal_id>.

    Plan 'free' no requiere PayPal — directamente actualiza la Subscription
    local y responde con redirect_url=null.
    """
    permission_classes = [IsAuthenticated, IsTenantAdminOrOwner]

    def post(self, request, slug: str):
        tenant = request.tenant
        plan = get_object_or_404(Plan, slug=slug, is_active=True, is_public=True)

        # Free → sin PayPal
        if plan.price_monthly == 0:
            from apps.tenants.serializers import _sync_subscription_with_plan
            tenant.plan = plan.slug
            tenant.save(update_fields=['plan'])
            _sync_subscription_with_plan(tenant)

            # Si tenía suscripción de pago activa, hay que cancelarla
            sub = getattr(tenant, 'subscription', None)
            if sub and sub.paypal_subscription_id:
                try:
                    get_paypal_client().cancel_subscription(
                        sub.paypal_subscription_id,
                        reason='Downgrade a plan gratuito',
                    )
                except PayPalError:
                    logger.exception('No se pudo cancelar suscripción PayPal en downgrade')
                sub.paypal_subscription_id = ''
                sub.paypal_plan_id = ''
                sub.save(update_fields=['paypal_subscription_id', 'paypal_plan_id', 'updated_at'])

            PaymentTransaction.objects.create(
                tenant=tenant,
                subscription=sub,
                plan=plan,
                event_type=PaymentEventType.SUBSCRIPTION_ACTIVATED,
                provider='internal',
                payload={'reason': 'free plan, no payment required'},
            )
            return Response({'redirect_url': None, 'plan': plan.slug, 'message': 'Plan gratuito activado.'})

        # Paid → necesita paypal_plan_id
        if not plan.paypal_plan_id:
            return Response(
                {
                    'error': 'Este plan aún no está sincronizado con PayPal.',
                    'detail': 'El super admin debe correr "Sincronizar planes" en su panel antes de que los tenants puedan suscribirse.',
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Construir return_url incluyendo el slug del tenant para no perder contexto
        return_url = settings.PAYPAL_RETURN_URL
        cancel_url = settings.PAYPAL_CANCEL_URL

        try:
            sub_data = get_paypal_client().create_subscription(
                plan_id=plan.paypal_plan_id,
                return_url=return_url,
                cancel_url=cancel_url,
                custom_id=str(tenant.id),
                subscriber_email=request.user.email,
                subscriber_name=request.user.get_full_name() or request.user.email,
                request_id=f'sub-{tenant.id}-{plan.slug}-{int(timezone.now().timestamp())}',
            )
        except PayPalError as e:
            logger.exception('Error creando subscription PayPal')
            return Response(
                {'error': 'No se pudo crear la suscripción en PayPal.', 'detail': e.data},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        approval_link = next(
            (l['href'] for l in sub_data.get('links', []) if l.get('rel') == 'approve'),
            None,
        )
        if not approval_link:
            return Response(
                {'error': 'PayPal no devolvió URL de aprobación.', 'detail': sub_data},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Pre-registramos la transacción aunque el usuario aún no apruebe.
        PaymentTransaction.objects.create(
            tenant=tenant,
            plan=plan,
            event_type=PaymentEventType.SUBSCRIPTION_CREATED,
            provider='paypal',
            provider_subscription_id=sub_data.get('id', ''),
            amount=plan.price_monthly,
            currency=plan.currency or 'MXN',
            payload=sub_data,
        )

        return Response({
            'redirect_url': approval_link,
            'subscription_id': sub_data.get('id'),
            'plan': plan.slug,
        })


# ── Return callback (tenant admin) ────────────────────────────────────────────


class PayPalReturnView(APIView):
    """
    GET /rest/v1/platform/paypal/return/?subscription_id=<paypal_sub_id>

    PayPal redirige al usuario aquí después de aprobar la suscripción.
    Validamos contra PayPal y actualizamos la Subscription local.

    Permission: IsAuthenticated. El tenant viene del request.
    """
    permission_classes = [IsAuthenticated, IsTenantAdminOrOwner]

    def get(self, request):
        paypal_sub_id = request.query_params.get('subscription_id')
        if not paypal_sub_id:
            return Response({'error': 'falta subscription_id'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = get_paypal_client().get_subscription(paypal_sub_id)
        except PayPalError as e:
            return Response({'error': 'No se pudo verificar con PayPal', 'detail': e.data},
                            status=status.HTTP_502_BAD_GATEWAY)

        return Response(_apply_paypal_subscription(request.tenant, data))


# ── Cancel (tenant admin) ─────────────────────────────────────────────────────


class PayPalCancelView(APIView):
    """
    POST /rest/v1/platform/paypal/cancel/  (body opcional: { "reason": "..." })
    Cancela la suscripción PayPal del tenant actual.
    Después del cancel, la Subscription local pasa a 'canceled' (lo confirmará
    también el webhook BILLING.SUBSCRIPTION.CANCELLED).
    """
    permission_classes = [IsAuthenticated, IsTenantAdminOrOwner]

    def post(self, request):
        tenant = request.tenant
        sub = getattr(tenant, 'subscription', None)
        if not sub or not sub.paypal_subscription_id:
            return Response({'error': 'No hay suscripción PayPal activa.'},
                            status=status.HTTP_404_NOT_FOUND)

        reason = (request.data.get('reason') or 'Cancelado por el cliente')[:127]
        try:
            get_paypal_client().cancel_subscription(sub.paypal_subscription_id, reason=reason)
        except PayPalError as e:
            return Response({'error': 'PayPal rechazó la cancelación.', 'detail': e.data},
                            status=status.HTTP_502_BAD_GATEWAY)

        sub.status = SubscriptionStatus.CANCELED
        sub.canceled_at = timezone.now().date()
        sub.save(update_fields=['status', 'canceled_at', 'updated_at'])

        PaymentTransaction.objects.create(
            tenant=tenant,
            subscription=sub,
            plan=sub.plan,
            event_type=PaymentEventType.SUBSCRIPTION_CANCELLED,
            provider='paypal',
            provider_subscription_id=sub.paypal_subscription_id,
            payload={'reason': reason},
        )
        return Response({'ok': True, 'status': sub.status})


# ── Webhook ───────────────────────────────────────────────────────────────────


WEBHOOK_EVENT_MAP = {
    'BILLING.SUBSCRIPTION.ACTIVATED': PaymentEventType.SUBSCRIPTION_ACTIVATED,
    'BILLING.SUBSCRIPTION.CREATED': PaymentEventType.SUBSCRIPTION_CREATED,
    'BILLING.SUBSCRIPTION.CANCELLED': PaymentEventType.SUBSCRIPTION_CANCELLED,
    'BILLING.SUBSCRIPTION.SUSPENDED': PaymentEventType.SUBSCRIPTION_SUSPENDED,
    'BILLING.SUBSCRIPTION.EXPIRED': PaymentEventType.SUBSCRIPTION_CANCELLED,
    'PAYMENT.SALE.COMPLETED': PaymentEventType.PAYMENT_COMPLETED,
    'PAYMENT.SALE.DENIED': PaymentEventType.PAYMENT_FAILED,
    'BILLING.SUBSCRIPTION.PAYMENT.FAILED': PaymentEventType.PAYMENT_FAILED,
}


class PayPalWebhookView(APIView):
    """
    POST /rest/v1/platform/paypal/webhook/

    Endpoint público al que PayPal manda eventos. Verificamos la firma con la
    API de PayPal antes de procesar. En desarrollo (sin PAYPAL_WEBHOOK_ID)
    aceptamos sin verificar y registramos warning.
    """
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        client = get_paypal_client()
        raw = request.body.decode('utf-8') if request.body else ''
        webhook_id = settings.PAYPAL_WEBHOOK_ID

        if webhook_id:
            verified = client.verify_webhook_signature(headers=request.META, raw_body=raw, webhook_id=webhook_id)
            if not verified:
                # Re-mapear headers del estilo Django (HTTP_PAYPAL_AUTH_ALGO) a estándar
                headers = {k.replace('HTTP_', '').replace('_', '-'): v
                           for k, v in request.META.items() if k.startswith('HTTP_PAYPAL')}
                verified = client.verify_webhook_signature(headers=headers, raw_body=raw, webhook_id=webhook_id)
            if not verified:
                logger.warning('Webhook PayPal con firma inválida')
                return Response({'error': 'invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            logger.warning('PAYPAL_WEBHOOK_ID no configurado — aceptando webhook sin verificar firma')

        event = request.data
        event_type = event.get('event_type', '')
        resource = event.get('resource', {}) or {}

        # Las suscripciones traen el ID en resource.id; los pagos también pero el sub link está en resource.billing_agreement_id
        paypal_sub_id = resource.get('id') if event_type.startswith('BILLING.SUBSCRIPTION.') else resource.get('billing_agreement_id')

        sub = None
        tenant = None
        if paypal_sub_id:
            sub = Subscription.objects.filter(paypal_subscription_id=paypal_sub_id).first()
            if sub:
                tenant = sub.tenant

        # Si tenemos sub, aplicamos cambio de status
        if sub and event_type in WEBHOOK_EVENT_MAP:
            mapped = WEBHOOK_EVENT_MAP[event_type]
            today = timezone.now().date()
            if mapped == PaymentEventType.SUBSCRIPTION_ACTIVATED:
                sub.status = SubscriptionStatus.ACTIVE
                sub.trial_ends_at = None
                sub.current_period_end = today + timedelta(days=30)
            elif mapped in (PaymentEventType.SUBSCRIPTION_CANCELLED,):
                sub.status = SubscriptionStatus.CANCELED
                sub.canceled_at = today
            elif mapped == PaymentEventType.SUBSCRIPTION_SUSPENDED:
                sub.status = SubscriptionStatus.SUSPENDED
            elif mapped == PaymentEventType.PAYMENT_COMPLETED:
                # Renovación mensual exitosa → extender período
                sub.status = SubscriptionStatus.ACTIVE
                sub.current_period_end = max(sub.current_period_end, today) + timedelta(days=30)
            elif mapped == PaymentEventType.PAYMENT_FAILED:
                sub.status = SubscriptionStatus.PAST_DUE
            sub.save(update_fields=['status', 'trial_ends_at', 'current_period_end', 'canceled_at', 'updated_at'])

        # Log
        amount = None
        currency = ''
        if 'amount' in resource and isinstance(resource['amount'], dict):
            try:
                amount = Decimal(resource['amount'].get('total') or resource['amount'].get('value') or '0')
                currency = resource['amount'].get('currency_code') or resource['amount'].get('currency') or ''
            except Exception:
                pass

        PaymentTransaction.objects.create(
            tenant=tenant,
            subscription=sub,
            plan=sub.plan if sub else None,
            event_type=WEBHOOK_EVENT_MAP.get(event_type, PaymentEventType.OTHER),
            provider='paypal',
            provider_event_id=event.get('id', ''),
            provider_subscription_id=paypal_sub_id or '',
            amount=amount,
            currency=currency,
            payload=event,
        )

        return Response({'ok': True}, status=status.HTTP_200_OK)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _apply_paypal_subscription(tenant, paypal_data: dict) -> dict:
    """
    Toma el cuerpo de GET /v1/billing/subscriptions/{id} y actualiza la
    Subscription local del tenant. Devuelve dict para responder al frontend.
    """
    paypal_id = paypal_data.get('id')
    plan_id = paypal_data.get('plan_id')
    paypal_status = paypal_data.get('status', 'APPROVAL_PENDING').upper()

    plan = Plan.objects.filter(paypal_plan_id=plan_id).first()
    if not plan:
        return {'ok': False, 'error': 'Plan PayPal no reconocido', 'paypal_status': paypal_status}

    today = timezone.now().date()
    sub, _ = Subscription.objects.get_or_create(
        tenant=tenant,
        defaults={
            'plan': plan,
            'billing_cycle': 'monthly',
            'started_at': today,
            'current_period_end': today + timedelta(days=30),
        },
    )
    sub.plan = plan
    sub.paypal_subscription_id = paypal_id
    sub.paypal_plan_id = plan_id

    if paypal_status in ('ACTIVE', 'APPROVED'):
        sub.status = SubscriptionStatus.ACTIVE
        sub.trial_ends_at = None
        sub.current_period_end = today + timedelta(days=30)
    elif paypal_status == 'APPROVAL_PENDING':
        sub.status = SubscriptionStatus.TRIAL
    elif paypal_status == 'CANCELLED':
        sub.status = SubscriptionStatus.CANCELED
        sub.canceled_at = today
    elif paypal_status == 'SUSPENDED':
        sub.status = SubscriptionStatus.SUSPENDED

    sub.save()

    # Sincroniza Tenant.plan también
    if tenant.plan != plan.slug:
        tenant.plan = plan.slug
        tenant.save(update_fields=['plan'])

    PaymentTransaction.objects.create(
        tenant=tenant,
        subscription=sub,
        plan=plan,
        event_type=PaymentEventType.SUBSCRIPTION_ACTIVATED if sub.status == SubscriptionStatus.ACTIVE else PaymentEventType.SUBSCRIPTION_CREATED,
        provider='paypal',
        provider_subscription_id=paypal_id or '',
        amount=plan.price_monthly,
        currency=plan.currency or 'MXN',
        payload=paypal_data,
    )

    return {
        'ok': True,
        'subscription_id': paypal_id,
        'plan': plan.slug,
        'status': sub.status,
    }
