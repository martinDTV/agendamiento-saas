from rest_framework import serializers

from .models import Branch, Doctor, Service, Schedule


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name', 'address', 'phone', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class DoctorSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    service_ids = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = [
            'id', 'user', 'email', 'full_name',
            'branch', 'branch_name',
            'specialty', 'bio', 'photo', 'appointment_duration',
            'service_ids',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'email', 'full_name', 'branch_name', 'service_ids', 'created_at']

    def get_service_ids(self, obj):
        return [str(s.id) for s in obj.services.all()]

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.email

    def validate(self, data):
        request = self.context.get('request')
        user = data.get('user')
        if request and user and not self.instance:
            if Doctor.objects.for_tenant(request.tenant).filter(user=user).exists():
                raise serializers.ValidationError(
                    {'user': 'Ya existe un perfil de doctor para este usuario en este tenant.'}
                )
        return data


class ServiceSerializer(serializers.ModelSerializer):
    doctor_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        source='doctors',
        queryset=Doctor._all.all(),
        required=False,
    )

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'duration', 'price', 'color',
            'doctor_ids',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['doctor_ids'] = [str(d_id) for d_id in data.get('doctor_ids', [])]
        return data

    def validate_doctor_ids(self, value):
        request = self.context.get('request')
        if request and getattr(request, 'tenant', None):
            for doctor in value:
                if doctor.tenant_id != request.tenant.id:
                    raise serializers.ValidationError('Doctor no pertenece a este tenant.')
        return value


class ScheduleSerializer(serializers.ModelSerializer):
    weekday_label = serializers.CharField(source='get_weekday_display', read_only=True)

    class Meta:
        model = Schedule
        fields = ['id', 'doctor', 'weekday', 'weekday_label', 'start_time', 'end_time', 'is_active']
        read_only_fields = ['id', 'weekday_label']

    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError(
                    {'end_time': 'La hora de fin debe ser posterior a la de inicio.'}
                )
        request = self.context.get('request')
        doctor = data.get('doctor')
        weekday = data.get('weekday')
        if request and doctor and weekday is not None and not self.instance:
            if Schedule.objects.for_tenant(request.tenant).filter(doctor=doctor, weekday=weekday).exists():
                raise serializers.ValidationError(
                    {'weekday': 'Ya existe un horario para este doctor en ese día.'}
                )
        return data
