"""
Cliente liviano para la API REST de PayPal v2 / Subscriptions API.

Documentación:
- OAuth: https://developer.paypal.com/api/rest/authentication/
- Catalog Products: https://developer.paypal.com/docs/api/catalog-products/v1/
- Subscriptions / Plans: https://developer.paypal.com/docs/api/subscriptions/v1/
- Webhooks verify: https://developer.paypal.com/docs/api/webhooks/v1/#verify-webhook-signature

Decisiones:
- Sin SDK (paypalrestsdk está deprecado). Solo `httpx` que ya está en requirements.
- Token cacheado en memoria por TTL. Para multi-proceso usar Redis después.
- Errores se elevan como PayPalError con el JSON de PayPal adjunto.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from django.conf import settings


class PayPalError(RuntimeError):
    """Error de PayPal con el cuerpo de la respuesta adjunto en .data."""

    def __init__(self, message: str, status_code: int = 0, data: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.data = data or {}


@dataclass
class _CachedToken:
    value: str = ''
    expires_at: float = 0.0  # epoch seconds

    def is_valid(self) -> bool:
        # 30s de margen antes de la expiración real
        return bool(self.value) and time.time() < self.expires_at - 30


class PayPalClient:
    """
    Singleton ligero. Lee credenciales de Django settings:
    - PAYPAL_CLIENT_ID, PAYPAL_SECRET, PAYPAL_API_BASE, PAYPAL_WEBHOOK_ID
    """

    _token: _CachedToken = field(default_factory=_CachedToken)

    def __init__(self):
        self._token = _CachedToken()

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _get_token(self) -> str:
        if self._token.is_valid():
            return self._token.value

        client_id = settings.PAYPAL_CLIENT_ID
        secret = settings.PAYPAL_SECRET
        if not client_id or not secret:
            raise PayPalError('PayPal no configurado: faltan PAYPAL_CLIENT_ID o PAYPAL_SECRET en .env')

        with httpx.Client(timeout=15) as client:
            r = client.post(
                f'{settings.PAYPAL_API_BASE}/v1/oauth2/token',
                auth=(client_id, secret),
                data={'grant_type': 'client_credentials'},
                headers={'Accept': 'application/json'},
            )

        if r.status_code != 200:
            raise PayPalError(
                f'OAuth fallido ({r.status_code})',
                status_code=r.status_code,
                data=_safe_json(r),
            )
        body = r.json()
        self._token = _CachedToken(
            value=body['access_token'],
            expires_at=time.time() + int(body.get('expires_in', 32400)),
        )
        return self._token.value

    def _headers(self, request_id: str | None = None) -> dict:
        h = {
            'Authorization': f'Bearer {self._get_token()}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if request_id:
            # Idempotencia para creates/updates
            h['PayPal-Request-Id'] = request_id
        return h

    # ── HTTP wrapper ──────────────────────────────────────────────────────────

    def _request(self, method: str, path: str, *, json: dict | None = None,
                 request_id: str | None = None, expected: tuple[int, ...] = (200, 201, 204)) -> dict:
        url = f'{settings.PAYPAL_API_BASE}{path}'
        with httpx.Client(timeout=20) as client:
            r = client.request(method, url, json=json, headers=self._headers(request_id))
        if r.status_code not in expected:
            raise PayPalError(
                f'PayPal {method} {path} → {r.status_code}',
                status_code=r.status_code,
                data=_safe_json(r),
            )
        if r.status_code == 204 or not r.content:
            return {}
        return r.json()

    # ── Catalog: Products ─────────────────────────────────────────────────────

    def create_product(self, *, name: str, description: str = '', category: str = 'SOFTWARE',
                       request_id: str | None = None) -> dict:
        """POST /v1/catalog/products"""
        return self._request('POST', '/v1/catalog/products', json={
            'name': name[:127],
            'description': description[:256] if description else '',
            'type': 'SERVICE',
            'category': category,
        }, request_id=request_id)

    # ── Subscriptions: Plans ──────────────────────────────────────────────────

    def create_billing_plan(self, *, product_id: str, name: str,
                            price_monthly: float, currency: str = 'MXN',
                            description: str = '', request_id: str | None = None) -> dict:
        """
        POST /v1/billing/plans — crea un plan de cobro recurrente mensual.
        El plan queda en status=CREATED. Hay que activarlo con activate_plan.
        """
        body = {
            'product_id': product_id,
            'name': name[:127],
            'description': (description or name)[:127],
            'status': 'ACTIVE',
            'billing_cycles': [{
                'frequency': {'interval_unit': 'MONTH', 'interval_count': 1},
                'tenure_type': 'REGULAR',
                'sequence': 1,
                'total_cycles': 0,  # 0 = infinito
                'pricing_scheme': {
                    'fixed_price': {
                        'value': f'{float(price_monthly):.2f}',
                        'currency_code': currency,
                    },
                },
            }],
            'payment_preferences': {
                'auto_bill_outstanding': True,
                'setup_fee_failure_action': 'CONTINUE',
                'payment_failure_threshold': 3,
            },
        }
        return self._request('POST', '/v1/billing/plans', json=body, request_id=request_id)

    def deactivate_plan(self, plan_id: str) -> None:
        """POST /v1/billing/plans/{id}/deactivate"""
        self._request('POST', f'/v1/billing/plans/{plan_id}/deactivate', expected=(204,))

    # ── Subscriptions ─────────────────────────────────────────────────────────

    def create_subscription(self, *, plan_id: str, return_url: str, cancel_url: str,
                            custom_id: str = '', subscriber_email: str = '',
                            subscriber_name: str = '',
                            request_id: str | None = None) -> dict:
        """
        POST /v1/billing/subscriptions
        Devuelve el objeto subscription con .id y .links (incluyendo el de aprobación).
        El usuario debe ir a links.rel=approve.href para aprobar.
        """
        body: dict[str, Any] = {
            'plan_id': plan_id,
            'application_context': {
                'brand_name': 'Agendamiento SaaS',
                'locale': 'es-MX',
                'shipping_preference': 'NO_SHIPPING',
                'user_action': 'SUBSCRIBE_NOW',
                'payment_method': {
                    'payer_selected': 'PAYPAL',
                    'payee_preferred': 'IMMEDIATE_PAYMENT_REQUIRED',
                },
                'return_url': return_url,
                'cancel_url': cancel_url,
            },
        }
        if custom_id:
            body['custom_id'] = custom_id[:127]
        if subscriber_email or subscriber_name:
            sub: dict = {}
            if subscriber_email:
                sub['email_address'] = subscriber_email
            if subscriber_name:
                # Best effort: si tiene espacio, divide
                parts = subscriber_name.strip().split(' ', 1)
                sub['name'] = {'given_name': parts[0], 'surname': parts[1] if len(parts) > 1 else parts[0]}
            body['subscriber'] = sub

        return self._request('POST', '/v1/billing/subscriptions', json=body, request_id=request_id)

    def get_subscription(self, subscription_id: str) -> dict:
        """GET /v1/billing/subscriptions/{id}"""
        return self._request('GET', f'/v1/billing/subscriptions/{subscription_id}')

    def cancel_subscription(self, subscription_id: str, reason: str = 'Cancelado por el usuario') -> None:
        """POST /v1/billing/subscriptions/{id}/cancel"""
        self._request(
            'POST',
            f'/v1/billing/subscriptions/{subscription_id}/cancel',
            json={'reason': reason[:127]},
            expected=(204,),
        )

    # ── Webhooks ──────────────────────────────────────────────────────────────

    def verify_webhook_signature(self, *, headers: dict, raw_body: str, webhook_id: str | None = None) -> bool:
        """
        POST /v1/notifications/verify-webhook-signature
        Devuelve True si la firma es válida.

        headers debe contener:
          PAYPAL-AUTH-ALGO, PAYPAL-CERT-URL, PAYPAL-TRANSMISSION-ID,
          PAYPAL-TRANSMISSION-SIG, PAYPAL-TRANSMISSION-TIME
        """
        webhook_id = webhook_id or settings.PAYPAL_WEBHOOK_ID
        if not webhook_id:
            return False

        # PayPal espera el `webhook_event` como dict, no como string
        import json as json_lib
        try:
            event = json_lib.loads(raw_body)
        except (TypeError, ValueError):
            return False

        body = {
            'auth_algo': headers.get('PAYPAL-AUTH-ALGO') or headers.get('paypal-auth-algo'),
            'cert_url': headers.get('PAYPAL-CERT-URL') or headers.get('paypal-cert-url'),
            'transmission_id': headers.get('PAYPAL-TRANSMISSION-ID') or headers.get('paypal-transmission-id'),
            'transmission_sig': headers.get('PAYPAL-TRANSMISSION-SIG') or headers.get('paypal-transmission-sig'),
            'transmission_time': headers.get('PAYPAL-TRANSMISSION-TIME') or headers.get('paypal-transmission-time'),
            'webhook_id': webhook_id,
            'webhook_event': event,
        }
        try:
            res = self._request('POST', '/v1/notifications/verify-webhook-signature', json=body)
        except PayPalError:
            return False
        return res.get('verification_status') == 'SUCCESS'


def _safe_json(r: httpx.Response) -> dict:
    try:
        return r.json()
    except Exception:
        return {'raw': r.text[:500]}


def get_paypal_client() -> PayPalClient:
    """Helper para obtener un cliente. Si después quieres cachearlo a nivel app, cámbialo aquí."""
    return PayPalClient()
