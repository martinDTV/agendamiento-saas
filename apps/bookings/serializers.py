from datetime import timedelta

from rest_framework import serializers

from apps.catalog.models import Doctor, Service
from .models import Appointment, AppointmentStatus


class SlotSerializer(serializers.Serializer):
    start = serializers.TimeField(format='%H:%M')
    end = serializers.TimeField(format='%H:%M')


class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor', 'service',
            'patient_name', 'patient_email', 'patient_phone',
            'date', 'start_time', 'notes',
        ]
        read_only_fields = ['id']

    def validate(self, data):
        doctor = data.get('doctor')
        service = data.get('service')
        date = data.get('date')
        start_time = data.get('start_time')

        if not all([doctor, service, date, start_time]):
            return data

        # Verify doctor belongs to same tenant
        tenant = self.context['request'].tenant
        if doctor.tenant_id != tenant.pk:
            raise serializers.ValidationError({'doctor': 'Doctor no válido.'})
        if service.tenant_id != tenant.pk:
            raise serializers.ValidationError({'service': 'Servicio no válido.'})

        # Calculate end_time from service duration
        from datetime import datetime
        start_dt = datetime.combine(date, start_time)
        data['end_time'] = (start_dt + timedelta(minutes=service.duration)).time()

        # Ensure slot is not already taken
        if Appointment.objects.for_tenant(tenant).filter(
            doctor=doctor,
            date=date,
            start_time=start_time,
            status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED],
        ).exists():
            raise serializers.ValidationError(
                {'start_time': 'Este horario ya no está disponible.'}
            )

        return data


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor', 'doctor_name', 'service', 'service_name',
            'patient_name', 'patient_email', 'patient_phone',
            'date', 'start_time', 'end_time',
            'status', 'notes',
            'clinical_notes', 'weight_kg', 'height_cm', 'blood_pressure',
            'heart_rate', 'temperature_c', 'oxygen_sat',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'doctor_name', 'service_name', 'end_time', 'created_at', 'updated_at']

    def get_doctor_name(self, obj):
        return str(obj.doctor)
