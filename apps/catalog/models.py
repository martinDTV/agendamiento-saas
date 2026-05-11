from django.conf import settings
from django.db import models

from shared.models import TenantScopedModel, TenantManager, UnscopedManager


class Branch(TenantScopedModel):
    """Physical location or consultorio belonging to a tenant."""

    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    _all = UnscopedManager()
    objects = TenantManager()

    class Meta(TenantScopedModel.Meta):
        ordering = ['name']
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'

    def __str__(self):
        return f'{self.name} ({self.tenant.slug})'


class Doctor(TenantScopedModel):
    """Doctor profile linked to a user within a tenant."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profiles',
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctors',
    )
    specialty = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='doctors/', blank=True, null=True)
    appointment_duration = models.PositiveIntegerField(
        default=30,
        help_text='Duración predeterminada de cita en minutos',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    _all = UnscopedManager()
    objects = TenantManager()

    class Meta(TenantScopedModel.Meta):
        ordering = ['user__last_name', 'user__first_name']
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctores'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'user'],
                name='unique_doctor_per_tenant',
            )
        ]

    def __str__(self):
        return f'Dr. {self.user.get_full_name() or self.user.email} ({self.tenant.slug})'


class Service(TenantScopedModel):
    """Service or procedure offered by the tenant."""

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(help_text='Duración en minutos')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=7, default='#3B82F6', help_text='Color hex para calendario')
    doctors = models.ManyToManyField(
        Doctor,
        related_name='services',
        blank=True,
        help_text='Doctores que ofrecen este servicio. Vacío = ninguno.',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    _all = UnscopedManager()
    objects = TenantManager()

    class Meta(TenantScopedModel.Meta):
        ordering = ['name']
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'

    def __str__(self):
        return f'{self.name} ({self.tenant.slug})'


class Schedule(TenantScopedModel):
    """Weekly availability block for a doctor."""

    class Weekday(models.IntegerChoices):
        MONDAY = 0, 'Lunes'
        TUESDAY = 1, 'Martes'
        WEDNESDAY = 2, 'Miércoles'
        THURSDAY = 3, 'Jueves'
        FRIDAY = 4, 'Viernes'
        SATURDAY = 5, 'Sábado'
        SUNDAY = 6, 'Domingo'

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='schedules',
    )
    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    _all = UnscopedManager()
    objects = TenantManager()

    class Meta(TenantScopedModel.Meta):
        ordering = ['doctor', 'weekday', 'start_time']
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'doctor', 'weekday'],
                name='unique_schedule_per_doctor_weekday',
            )
        ]

    def __str__(self):
        return f'{self.doctor} — {self.get_weekday_display()} {self.start_time}–{self.end_time}'
