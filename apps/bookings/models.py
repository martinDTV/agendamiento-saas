from django.db import models

from shared.models import TenantScopedModel, TenantManager, UnscopedManager


class AppointmentStatus(models.TextChoices):
    PENDING = 'pending', 'Pendiente'
    CONFIRMED = 'confirmed', 'Confirmada'
    CANCELLED = 'cancelled', 'Cancelada'
    COMPLETED = 'completed', 'Completada'


class Appointment(TenantScopedModel):
    """A booked appointment between a patient and a doctor."""

    doctor = models.ForeignKey(
        'catalog.Doctor',
        on_delete=models.PROTECT,
        related_name='appointments',
    )
    service = models.ForeignKey(
        'catalog.Service',
        on_delete=models.PROTECT,
        related_name='appointments',
    )
    # ── Paciente ────────────────────────────────────────────────────────────
    # `patient` (FK opcional a apps.patients.Patient) se llena cuando el paciente
    # reserva CON cuenta. Los campos `patient_name/email/phone` son fallback
    # cuando reserva SIN cuenta (booking público anónimo). Mantenemos ambos:
    # eventualmente, cuando todos los pacientes tengan cuenta, una data
    # migration borrará los strings y dejará solo el FK.
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
    )
    patient_name = models.CharField(max_length=150)
    patient_email = models.EmailField()
    patient_phone = models.CharField(max_length=20, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PENDING,
    )
    notes = models.TextField(blank=True, help_text='Notas internas')

    # ── Clinical record (filled in by the doctor during/after the visit) ────
    clinical_notes = models.TextField(blank=True, help_text='Apuntes médicos y observaciones')
    weight_kg      = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height_cm      = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    blood_pressure = models.CharField(max_length=15, blank=True, help_text='Ej. 120/80')
    heart_rate     = models.PositiveIntegerField(null=True, blank=True, help_text='lpm')
    temperature_c  = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    oxygen_sat     = models.PositiveSmallIntegerField(null=True, blank=True, help_text='%')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    _all = UnscopedManager()
    objects = TenantManager()

    class Meta(TenantScopedModel.Meta):
        ordering = ['date', 'start_time']
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'doctor', 'date', 'start_time'],
                name='unique_appointment_slot',
            )
        ]

    def __str__(self):
        return f'{self.patient_name} con {self.doctor} el {self.date} {self.start_time}'
