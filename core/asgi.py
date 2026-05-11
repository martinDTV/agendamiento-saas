"""
ASGI config for core project.

Routes:
- HTTP → Django (DRF, normal views)
- WebSocket → Channels with chat consumers (visitor / support)
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Initialize Django ASGI app early so that AppRegistry is ready before importing
# anything that depends on ORM models (like our consumers).
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

from apps.support.routing import websocket_urlpatterns  # noqa: E402
from apps.support.middleware import TokenAuthMiddleware  # noqa: E402


application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        TokenAuthMiddleware(URLRouter(websocket_urlpatterns))
    ),
})
