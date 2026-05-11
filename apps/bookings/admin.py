from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient_name', 'doctor', 'service', 'date', 'start_time', 'status', 'tenant']
    list_filter = ['status', 'date', 'tenant']
    search_fields = ['patient_name', 'patient_email']
    date_hierarchy = 'date'
