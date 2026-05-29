"""
Rutas autenticadas de la app patients (perfil, mis citas).

Las rutas públicas (register, activate) viven en `public_urls.py` y se montan
bajo /rest/v1/public/patients/ desde apirest/urls.py.
"""
from django.urls import path

from . import views


app_name = 'patients'

urlpatterns = [
    path('me/', views.PatientMeView.as_view(), name='me'),
    path('me/appointments/', views.PatientMyAppointmentsView.as_view(), name='my-appointments'),
    path(
        'me/appointments/<uuid:appointment_id>/',
        views.PatientAppointmentDetailView.as_view(),
        name='appointment-detail',
    ),
]
