from django.contrib import admin

from .models import Patient, PatientActivationToken


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'gender', 'created_at']
    list_filter = ['gender', 'blood_type', 'address_state']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'phone', 'curp', 'rfc']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['user']
    fieldsets = (
        ('Cuenta', {'fields': ('user',)}),
        ('Básicos', {'fields': ('phone', 'birth_date', 'gender')}),
        ('Clínicos', {
            'fields': ('blood_type', 'allergies', 'current_medications', 'medical_conditions'),
        }),
        ('Dirección', {
            'fields': (
                'address_street', 'address_city', 'address_state',
                'address_zip', 'address_country',
            ),
            'classes': ('collapse',),
        }),
        ('Contacto de emergencia', {
            'fields': (
                'emergency_contact_name',
                'emergency_contact_phone',
                'emergency_contact_relation',
            ),
            'classes': ('collapse',),
        }),
        ('Identificación MX', {
            'fields': ('curp', 'rfc'),
            'classes': ('collapse',),
        }),
        ('Meta', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(PatientActivationToken)
class PatientActivationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_at', 'used_at']
    list_filter = ['used_at']
    search_fields = ['user__email']
    readonly_fields = ['token', 'created_at']
