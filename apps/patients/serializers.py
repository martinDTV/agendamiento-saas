"""Serializers para la app patients."""
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Patient, PatientActivationToken
from .validators import (
    normalize_curp,
    normalize_phone_mx,
    normalize_rfc,
    normalize_zip_mx,
)

User = get_user_model()


class PatientRegisterSerializer(serializers.Serializer):
    """
    Registro público de pacientes. Crea User (is_active=False) + Patient
    + PatientActivationToken atómicamente.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    # `phone` lo aceptamos sin maxLength estricto y normalizamos abajo —
    # el usuario puede escribir "+52 55 1234 5678" y queda "5512345678".
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                'Ya existe una cuenta con este correo.'
            )
        return email

    def validate_phone(self, value):
        # Normalizar y validar. Si está vacío, dejarlo vacío (phone es opcional
        # en registro — el paciente puede llenarlo después en su perfil).
        normalized = normalize_phone_mx(value)
        if not normalized:
            return ''
        from .validators import phone_mx_validator
        phone_mx_validator(normalized)  # lanza ValidationError si no cumple
        return normalized

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        # `users.User` extiende AbstractUser → tiene username obligatorio.
        # Usamos el email como username para satisfacer el constraint
        # unique_username_email del paquete.
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_active=False,  # debe activar por email
        )
        patient = Patient.objects.create(
            user=user,
            phone=validated_data.get('phone', ''),
            birth_date=validated_data.get('birth_date'),
        )
        activation = PatientActivationToken.objects.create(user=user)
        return {'patient': patient, 'activation': activation}


class PatientSerializer(serializers.ModelSerializer):
    """Serializer completo de Patient — para GET/PATCH /patients/me/."""
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    full_name = serializers.CharField(read_only=True)

    # Sobreescribimos max_length de phone/zip para permitir que entren strings
    # "sucios" ("+52 55 1234 5678", "CP 06000") que LUEGO normalizaremos en los
    # validate_* methods. El modelo guarda solo la versión limpia (10 dígitos,
    # 5 dígitos) y SUS validators rechazan cualquier otra cosa.
    phone = serializers.CharField(max_length=25, required=False, allow_blank=True)
    emergency_contact_phone = serializers.CharField(max_length=25, required=False, allow_blank=True)
    address_zip = serializers.CharField(max_length=10, required=False, allow_blank=True)
    # CURP y RFC también: el usuario puede meter espacios entre grupos.
    curp = serializers.CharField(max_length=25, required=False, allow_blank=True)
    rfc = serializers.CharField(max_length=18, required=False, allow_blank=True)

    class Meta:
        model = Patient
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'phone',
            'birth_date',
            'gender',
            'blood_type',
            'allergies',
            'current_medications',
            'medical_conditions',
            'address_street',
            'address_neighborhood',
            'address_city',
            'address_state',
            'address_zip',
            'address_country',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relation',
            'curp',
            'rfc',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # ── Normalización + validación explícita ─────────────────────────────
    # Como sobrescribimos los CharField del ModelSerializer (con max_length
    # más generoso para que entre el input "sucio"), DRF NO hereda los
    # `validators=[regex]` del modelo. Por eso aquí, después de normalizar,
    # disparamos el validator manualmente. Si falla, DRF convierte el
    # `ValidationError` en {"campo": ["mensaje"]} con 400.

    def _apply(self, normalizer, validator, value):
        """Helper: normaliza el valor y, si no quedó vacío, valida formato."""
        normalized = normalizer(value)
        if normalized:
            validator(normalized)
        return normalized

    def validate_curp(self, value):
        from .validators import curp_validator
        return self._apply(normalize_curp, curp_validator, value)

    def validate_rfc(self, value):
        from .validators import rfc_validator
        return self._apply(normalize_rfc, rfc_validator, value)

    def validate_phone(self, value):
        from .validators import phone_mx_validator
        return self._apply(normalize_phone_mx, phone_mx_validator, value)

    def validate_emergency_contact_phone(self, value):
        from .validators import phone_mx_validator
        return self._apply(normalize_phone_mx, phone_mx_validator, value)

    def validate_address_zip(self, value):
        from .validators import zip_mx_validator
        return self._apply(normalize_zip_mx, zip_mx_validator, value)

    def update(self, instance, validated_data):
        # first_name/last_name viven en User
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ActivatePatientSerializer(serializers.Serializer):
    """Activa al paciente usando el token enviado por email."""
    token = serializers.UUIDField()

    def validate_token(self, value):
        try:
            activation = PatientActivationToken.objects.select_related('user').get(token=value)
        except PatientActivationToken.DoesNotExist:
            raise serializers.ValidationError('Token inválido.')

        if activation.is_used:
            raise serializers.ValidationError('Este token ya fue utilizado.')
        if activation.is_expired:
            raise serializers.ValidationError('Este token ha expirado.')

        self.context['activation'] = activation
        return value

    @transaction.atomic
    def save(self):
        activation: PatientActivationToken = self.context['activation']
        from django.utils import timezone
        user = activation.user
        user.is_active = True
        user.save(update_fields=['is_active'])
        activation.used_at = timezone.now()
        activation.save(update_fields=['used_at'])
        return user
