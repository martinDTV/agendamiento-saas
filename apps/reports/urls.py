from django.urls import path

from .views import AppointmentReportExcelView, AppointmentReportView

urlpatterns = [
    path('appointments/', AppointmentReportView.as_view(), name='report-appointments'),
    path('appointments/export/', AppointmentReportExcelView.as_view(), name='report-appointments-export'),
]
