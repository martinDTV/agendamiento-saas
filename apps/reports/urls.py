from django.urls import path
from .views import AppointmentReportView

urlpatterns = [
    path('appointments/', AppointmentReportView.as_view(), name='report-appointments'),
]
