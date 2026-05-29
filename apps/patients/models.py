"""
Modelo `Patient` — paciente global (cross-clínica) del SaaS.

A diferencia del staff (que vive en `apps/accounts/Membership` ligado a un tenant),
un paciente es global: puede reservar citas en CUALQUIER clínica del SaaS usando la
misma cuenta. La relación paciente↔clínica emerge de los `Appointment` que tiene.

Por eso este modelo NO hereda de `TenantScopedModel`.

El paciente se identifica por su `User` (`AUTH_USER_MODEL` = 'users.User', email único).
Un User puede tener perfil de Patient O memberships de staff — son orthogonales.
"""
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from .validators import (
    curp_validator,
    phone_mx_validator,
    rfc_validator,
    zip_mx_validator,
)


class Gender(models.TextChoices):
    MALE = 'male', 'Masculino'
    FEMALE = 'female', 'Femenino'
    OTHER = 'other', 'Otro'
    UNDISCLOSED = 'undisclosed', 'Prefiero no decir'


class BloodType(models.TextChoices):
    A_POS = 'A+', 'A+'
    A_NEG = 'A-', 'A-'
    B_POS = 'B+', 'B+'
    B_NEG = 'B-', 'B-'
    AB_POS = 'AB+', 'AB+'
    AB_NEG = 'AB-', 'AB-'
    O_POS = 'O+', 'O+'
    O_NEG = 'O-', 'O-'
    UNKNOWN = 'unknown', 'Desconocido'


class Patient(models.Model):
    """
    Perfil de paciente. OneToOne con el User del paquete `users`.

    Es un modelo GLOBAL — no pertenece a ningún tenant.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile',
    )

    # ── Básicos ─────────────────────────────────────────────────────────────
    # first_name/last_name viven en User, pero aquí guardamos el teléfono
    # porque no está en User y todo paciente debe tener uno para contactarlo.
    #
    # `phone` se almacena NORMALIZADO (10 dígitos crudos, sin '+52' ni espacios).
    # max_length=10 es estricto a propósito — el serializer normaliza antes de
    # validar, así que cualquier input válido cabe en 10 chars.
    phone = models.CharField(
        max_length=10,
        blank=True,
        validators=[phone_mx_validator],
        help_text='10 dígitos (con lada). Ej. 5512345678',
    )
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        blank=True,
    )

    # ── Clínicos (opcionales — el paciente los completa cuando quiere) ──────
    blood_type = models.CharField(
        max_length=10,
        choices=BloodType.choices,
        blank=True,
    )
    allergies = models.TextField(
        blank=True,
        help_text='Alergias conocidas (medicamentos, alimentos, etc.)',
    )
    current_medications = models.TextField(
        blank=True,
        help_text='Medicamentos que toma actualmente',
    )
    medical_conditions = models.TextField(
        blank=True,
        help_text='Condiciones crónicas o relevantes',
    )

    # ── Dirección ───────────────────────────────────────────────────────────
    # En México la dirección típica tiene: calle+número exterior+interior,
    # colonia (asentamiento), ciudad (municipio), estado, CP. La colonia es
    # un campo CRÍTICO — sin ella no se entrega correo en muchas zonas.
    address_street = models.CharField(
        max_length=200, blank=True,
        help_text='Calle, número exterior y opcional interior.',
    )
    address_neighborhood = models.CharField(
        max_length=120, blank=True,
        help_text='Colonia o asentamiento (ej. Palo de Rosa, Roma Norte).',
    )
    address_city = models.CharField(
        max_length=100, blank=True,
        help_text='Ciudad o municipio (ej. Ciudad Valles, CDMX).',
    )
    address_state = models.CharField(max_length=100, blank=True)
    address_zip = models.CharField(
        max_length=5,
        blank=True,
        validators=[zip_mx_validator],
        help_text='5 dígitos.',
    )
    address_country = models.CharField(max_length=100, blank=True, default='México')

    # ── Contacto de emergencia ──────────────────────────────────────────────
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(
        max_length=10,
        blank=True,
        validators=[phone_mx_validator],
        help_text='10 dígitos (con lada).',
    )
    emergency_contact_relation = models.CharField(
        max_length=50,
        blank=True,
        help_text='Ej. Madre, Cónyuge, Hermano',
    )

    # ── Identificación MX ───────────────────────────────────────────────────
    # CURP: 18 caracteres exactos con formato estricto del RENAPO.
    # RFC: 13 caracteres exactos para persona física (paciente = siempre física).
    # Ambos validados por regex en `validators.py`. Se almacenan SIEMPRE en
    # mayúsculas — el serializer normaliza antes de validar.
    curp = models.CharField(
        max_length=18,
        blank=True,
        db_index=True,
        validators=[curp_validator],
        help_text='18 caracteres. Ej. PEPJ800101HDFRRR01',
    )
    rfc = models.CharField(
        max_length=13,
        blank=True,
        validators=[rfc_validator],
        help_text='13 caracteres. Ej. PEPJ800101AB1',
    )

    # ── Meta ─────────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} <{self.user.email}>'

    @property
    def full_name(self) -> str:
        full = f'{self.user.first_name} {self.user.last_name}'.strip()
        return full or self.user.email

    @property
    def email(self) -> str:
        return self.user.email


def _default_activation_expires():
    return timezone.now() + timedelta(days=7)


class PatientActivationToken(models.Model):
    """
    Token de activación enviado por email al paciente recién registrado.

    El paciente se crea con `is_active=False` y este token se manda al correo.
    Al hacer click se activa la cuenta (`is_active=True`) y se invalida el token.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_activation_tokens',
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    expires_at = models.DateTimeField(default=_default_activation_expires)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Token de activación de paciente'
        verbose_name_plural = 'Tokens de activación de pacientes'
        ordering = ['-created_at']

    def __str__(self):
        return f'ActivationToken({self.user.email}, used={self.used_at is not None})'

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired
