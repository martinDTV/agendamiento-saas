from django.contrib import admin

from .models import Branch, Doctor, Service, Schedule


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'phone', 'is_active']
    list_filter = ['is_active', 'tenant']
    search_fields = ['name', 'address']


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'specialty', 'branch', 'is_active']
    list_filter = ['is_active', 'tenant']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'specialty']
    raw_id_fields = ['user', 'branch']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'duration', 'price', 'doctor_count', 'is_active']
    list_filter = ['is_active', 'tenant']
    search_fields = ['name']
    filter_horizontal = ['doctors']

    def doctor_count(self, obj):
        return obj.doctors.count()
    doctor_count.short_description = 'Doctores'


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'weekday', 'start_time', 'end_time', 'is_active']
    list_filter = ['weekday', 'is_active', 'tenant']
