import json

from django.contrib.auth import get_user_model
from django.urls import path, include
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from users.viewsets import (
    RegisterViewSet,
    AuthTokenViewset,
    LogoutViewset,
    TokenRefreshViewSet,
    UserViewSet,
)
from apps.platform.views import PublicPlanListView
from apirest.uploads import LogoUploadView

app_name = 'apirest'

User = get_user_model()


def _peek_email_from_request(request) -> str | None:
    """
    Lee el email de la request SIN consumir el stream de DRF. Si tocamos
    request.data acá, el JWT view downstream falla con
    "You cannot access body after reading from request's data stream".

    Estrategia: leer request._request.body (Django cachea los bytes) y parsear
    JSON manualmente. Como Django guarda el body en cache la primera vez,
    DRF puede re-parsearlo después sin problemas.
    """
    try:
        raw = request._request.body
    except Exception:
        return None

    if not raw:
        return None

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError, TypeError):
        # Si viene como form-data, intentamos POST
        return (request._request.POST.get('email') or '').strip().lower() or None

    email = payload.get('email') if isinstance(payload, dict) else None
    return (email or '').strip().lower() or None


class TenantAuthTokenViewset(AuthTokenViewset):
    """
    Wrapper sobre AuthTokenViewset (django-users-auth) que:
    1. Pre-chequea si la cuenta existe pero está inactiva (no fue activada por email)
       → devuelve 403 con code 'activation_required' para que el frontend muestre
       un mensaje específico en lugar de "credenciales inválidas".
    2. Rechaza superusuarios (deben usar /platform/auth/login/).
    """
    def create(self, request):
        email = _peek_email_from_request(request)
        must_change_password = False
        if email:
            user = User.objects.filter(email__iexact=email).first()
            if user and not user.is_active:
                return Response(
                    {
                        'code': 'activation_required',
                        'error': 'Tu cuenta aún no fue activada. Revisá el correo enviado a esta dirección y haz click en el enlace de activación.',
                        'email': user.email,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            if user and hasattr(user, 'password_change_required'):
                must_change_password = True

        response = super().create(request)
        if response.status_code == status.HTTP_200_OK:
            if response.data.get('is_superuser'):
                return Response(
                    {'error': 'Los superusuarios deben iniciar sesión en el panel de plataforma.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            response.data['must_change_password'] = must_change_password
            # Inyectar datos del user para que el cliente móvil pueda saludar
            # con el nombre y pre-llenar el booking. La lib django-users-auth
            # solo devuelve user_id/uuid/is_superuser; aquí enriquecemos.
            if email:
                user = User.objects.filter(email__iexact=email).first()
                if user:
                    response.data['user'] = {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name or '',
                        'last_name': user.last_name or '',
                    }
        return response


router = DefaultRouter()

# ── Auth (django-users-auth) ──────────────────────────────────────────────────
router.register(r'user/auth/register', RegisterViewSet, basename='auth-register')
router.register(r'user/auth/login', TenantAuthTokenViewset, basename='auth-login')
router.register(r'user/auth/logout', LogoutViewset, basename='auth-logout')
router.register(r'user/auth/refresh-token', TokenRefreshViewSet, basename='auth-refresh')
router.register(r'user', UserViewSet, basename='user')

# ── Tenants ───────────────────────────────────────────────────────────────────
urlpatterns = [
    path('', include(router.urls)),
    path('tenants/', include('apps.tenants.urls', namespace='tenants')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('catalog/', include('apps.catalog.urls', namespace='catalog')),
    path('bookings/', include('apps.bookings.urls', namespace='bookings')),
    path('public/', include('apps.bookings.public_urls')),
    # ── Pacientes ──────────────────────────────────────────────────────────
    # /public/patients/...  → register, activate (sin auth)
    # /patients/me/...      → perfil, mis citas (con auth)
    path('public/patients/', include('apps.patients.public_urls')),
    path('patients/', include('apps.patients.urls', namespace='patients')),
    # ── Discover (cross-clínica, sin tenant) ───────────────────────────────
    # Endpoints que la app móvil consume sin saber a qué clínica pertenece.
    # Devuelven listas globales de doctores/clínicas con tenant_slug incluido.
    path('public/discover/', include('apps.catalog.discover_urls')),
    # ── Places (autocomplete de direcciones por CP) ────────────────────────
    # Usa zippopotam.us + Google Places API New (en cascada).
    path('public/places/', include('apps.places.urls')),
    # ── Reviews de doctores ────────────────────────────────────────────────
    path('public/reviews/', include('apps.reviews.public_urls')),
    path('reviews/', include('apps.reviews.urls', namespace='reviews')),
    # ── Leads / solicitudes de contacto desde la landing ───────────────────
    path('public/leads/', include('apps.leads.public_urls')),
    path('reports/', include('apps.reports.urls')),
    path('public/ai/', include('apps.ai.urls')),
    path('meetings/', include('apps.meetings.urls', namespace='meetings')),
    path('platform/', include('apps.platform.urls', namespace='platform')),
    path('support/', include('apps.support.urls', namespace='support')),
    path('plans/', PublicPlanListView.as_view(), name='public-plans'),
    path('uploads/logo/', LogoUploadView.as_view(), name='upload-logo'),
]

# Rutas resultantes:
#   POST /rest/v1/user/auth/register/          → RegisterViewSet.create
#   POST /rest/v1/user/auth/login/             → AuthTokenViewset.create  (email + password → tokens)
#   POST /rest/v1/user/auth/logout/            → LogoutViewset.create     (blacklist refresh)
#   POST /rest/v1/user/auth/refresh-token/     → TokenRefreshViewSet.create
#   GET  /rest/v1/user/                        → UserViewSet.list
#   GET  /rest/v1/user/{id}/                   → UserViewSet.retrieve
#   GET  /rest/v1/tenants/resolve/{slug}/      → TenantResolveView (público, SSR)
