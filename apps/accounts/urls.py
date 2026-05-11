from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.accounts import views

app_name = 'accounts'

router = DefaultRouter()
router.register(r'memberships', views.MembershipViewSet, basename='membership')
router.register(r'invitations', views.InvitationViewSet, basename='invitation')

urlpatterns = [
    path('register/', views.TenantRegistrationView.as_view(), name='register'),
    path('me/', views.MeView.as_view(), name='me'),
    path('me/profile-picture/', views.ProfilePictureView.as_view(), name='me-profile-picture'),
    path('activate/<uuid:token>/', views.ActivateAccountView.as_view(), name='activate'),
    path('', include(router.urls)),
]

# Rutas resultantes:
#   POST /rest/v1/accounts/register/                          → crear tenant + owner
#   GET  /rest/v1/accounts/me/                                → usuario actual + memberships
#   GET  /rest/v1/accounts/memberships/                       → listar miembros del tenant
#   PATCH/DELETE /rest/v1/accounts/memberships/{id}/          → editar/desactivar miembro
#   POST /rest/v1/accounts/invitations/                       → crear invitación
#   GET  /rest/v1/accounts/invitations/                       → listar invitaciones pendientes
#   POST /rest/v1/accounts/invitations/accept/{token}/        → aceptar invitación
