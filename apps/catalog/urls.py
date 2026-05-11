from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BranchViewSet, DoctorViewSet, ServiceViewSet, ScheduleViewSet

app_name = 'catalog'

router = DefaultRouter()
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'schedules', ScheduleViewSet, basename='schedule')

urlpatterns = [
    path('', include(router.urls)),
]

# Rutas resultantes:
#   GET/POST   /rest/v1/catalog/branches/
#   GET/PATCH/DELETE /rest/v1/catalog/branches/{id}/
#   GET/POST   /rest/v1/catalog/doctors/
#   GET/PATCH/DELETE /rest/v1/catalog/doctors/{id}/
#   GET/POST   /rest/v1/catalog/services/
#   GET/PATCH/DELETE /rest/v1/catalog/services/{id}/
#   GET/POST   /rest/v1/catalog/schedules/?doctor={id}
#   GET/PATCH/DELETE /rest/v1/catalog/schedules/{id}/
