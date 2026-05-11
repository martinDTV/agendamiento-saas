from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.catalog.views import PublicDoctorViewSet, PublicServiceViewSet
from .views import SlotsView, PublicAppointmentCreateView

router = DefaultRouter()
router.register(r'catalog/doctors', PublicDoctorViewSet, basename='public-doctor')
router.register(r'catalog/services', PublicServiceViewSet, basename='public-service')

urlpatterns = [
    path('', include(router.urls)),
    path('slots/', SlotsView.as_view(), name='slots'),
    path('appointments/', PublicAppointmentCreateView.as_view(), name='appointment-create'),
]
