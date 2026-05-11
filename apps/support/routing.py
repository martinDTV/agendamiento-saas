from django.urls import re_path

from . import consumers


websocket_urlpatterns = [
    re_path(r'ws/support/visitor/$', consumers.VisitorConsumer.as_asgi()),
    re_path(r'ws/support/agent/$', consumers.SupportConsumer.as_asgi()),
]
