from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.tenants import views

app_name = 'tenants'

router = DefaultRouter()
router.register(r'', views.TenantViewSet, basename='tenant')

urlpatterns = [
    path('me/', views.TenantSelfView.as_view(), name='tenant-me'),
    path('resolve/<slug:slug>/', views.TenantResolveView.as_view({'get': 'resolve'}), name='tenant-resolve'),
    path('', include(router.urls)),
]

# Routes:
#   GET  /rest/v1/tenants/resolve/{slug}/    → TenantResolveView  (public, SSR)
#   GET  /rest/v1/tenants/me/               → TenantSelfView      (admin/owner)
#   GET  /rest/v1/tenants/                  → TenantViewSet list   (superuser)
#   GET  /rest/v1/tenants/{slug}/           → TenantViewSet detail (superuser)
