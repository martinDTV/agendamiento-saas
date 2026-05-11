"""
Channels middleware: autentica el WebSocket vía JWT en query string.

El frontend abre la conexión con `?token=<jwt_access>&tenant=<slug>`.
- token (opcional): JWT del usuario; si está presente y es válido, scope['user']
  apunta al usuario; si no, AnonymousUser.
- tenant (requerido): slug del tenant — lo resolvemos a un objeto Tenant y
  lo guardamos en scope['tenant'].

El path del visitante (público) acepta scope sin token; el de agentes lo exige.
"""

import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.tenants.models import Tenant


User = get_user_model()
logger = logging.getLogger(__name__)


@database_sync_to_async
def _get_user_from_token(token: str):
    if not token:
        logger.info('WS auth: no token provided')
        return AnonymousUser()
    try:
        access = AccessToken(token)
        user_id = access.get('user_id')
        user = User.objects.filter(pk=user_id).first() if user_id else None
        if not user:
            logger.warning('WS auth: token valid but user_id=%s not found', user_id)
            return AnonymousUser()
        logger.info('WS auth: resolved user %s (id=%s)', user.email, user.pk)
        return user
    except TokenError as e:
        logger.warning('WS auth: TokenError %s', e)
        return AnonymousUser()
    except Exception as e:
        logger.warning('WS auth: unexpected error %s', e)
        return AnonymousUser()


@database_sync_to_async
def _get_tenant_by_slug(slug: str):
    if not slug:
        return None
    return Tenant.objects.filter(slug=slug, is_active=True).first()


class TokenAuthMiddleware(BaseMiddleware):
    """
    Inyecta scope['user'] y scope['tenant'] desde la query string del WebSocket.
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)

        token = (params.get('token') or [None])[0]
        tenant_slug = (params.get('tenant') or [None])[0]

        scope['user'] = await _get_user_from_token(token) if token else AnonymousUser()
        scope['tenant'] = await _get_tenant_by_slug(tenant_slug) if tenant_slug else None

        return await super().__call__(scope, receive, send)
