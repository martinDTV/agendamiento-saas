from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from django.views.static import serve


def health(_request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('dadmin/', admin.site.urls),
    path('rest/v1/', include('apirest.urls', namespace='apirest')),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('health/', health),
    path('', include('django_prometheus.urls')),
]

# Media servida por Django también con DEBUG=False: en este stack no hay
# nginx/S3 — Caddy proxya /media/* directo al backend (deploy/demo/Caddyfile).
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
