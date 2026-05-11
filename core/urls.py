from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health(_request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('dadmin/', admin.site.urls),
    path('rest/v1/', include('apirest.urls', namespace='apirest')),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('health/', health),
    path('', include('django_prometheus.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
