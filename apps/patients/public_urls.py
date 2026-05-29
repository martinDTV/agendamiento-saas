"""Rutas públicas (sin auth) de la app patients."""
from django.urls import path

from . import views


app_name = 'patients_public'

urlpatterns = [
    path('register/', views.PatientRegisterView.as_view(), name='register'),
    path('activate/', views.PatientActivateView.as_view(), name='activate'),
]
