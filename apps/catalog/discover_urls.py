"""URLs de los endpoints discover (cross-clínica)."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .discover_views import (
    DiscoverClinicsView,
    DiscoverDoctorsView,
    DiscoverServicesView,
)


router = DefaultRouter()
router.register(r'doctors', DiscoverDoctorsView, basename='discover-doctor')
router.register(r'clinics', DiscoverClinicsView, basename='discover-clinic')
router.register(r'services', DiscoverServicesView, basename='discover-service')

urlpatterns = [
    path('', include(router.urls)),
]

# Rutas resultantes:
#   GET /rest/v1/public/discover/doctors/          → todos los doctores activos
#   GET /rest/v1/public/discover/doctors/?tenant=clinica-a&specialty=...&q=...
#   GET /rest/v1/public/discover/clinics/          → todas las clínicas activas
#   GET /rest/v1/public/discover/services/?doctor=<id> → servicios del doctor
