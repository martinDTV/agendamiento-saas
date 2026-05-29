"""
Reseñas de doctores.

Dos caminos de creación:
  1. **Paciente autenticado** — POST /reviews/ con JWT → Review se publica.
     Patient FK obligatorio en ese camino. Único por (patient, doctor).
  2. **Anónimo con verificación de email** — POST /public/reviews/ sin auth →
     crea PendingReview con token UUID, manda correo. Al hacer click en el
     link del correo, se promueve a Review (patient=NULL, reviewer_name
     + reviewer_email preservados).

NO scoped por tenant porque las reviews siguen al doctor cross-clínica (si
el doctor cambia de clínica, su rating viaja con él).
"""
import uuid
from datetime import timedelta

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone


class Review(models.Model):
    # `patient` ahora es OPCIONAL — null cuando la reseña vino del flujo
    # anónimo verificado por email. En ese caso usamos reviewer_name/email.
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='reviews_given',
    )

    # Datos del autor cuando NO está vinculado a un Patient.
    # Si patient está set, estos se pueden ignorar (pero los llenamos copy
    # de user.email/name por conveniencia al consultar).
    reviewer_name = models.CharField(
        max_length=150, blank=True,
        help_text='Nombre del autor (visible). Cuando hay `patient`, '
                  'se llena con su nombre. En reseñas anónimas, es lo '
                  'que el usuario escribió.',
    )
    reviewer_email = models.EmailField(
        blank=True,
        help_text='Email del autor — usado para verificar reseñas anónimas '
                  'y para dedupe (un email = una reseña por doctor).',
    )

    doctor = models.ForeignKey(
        'catalog.Doctor',
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    appointment = models.ForeignKey(
        'bookings.Appointment',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviews',
        help_text='Cita que motivó la reseña. Opcional pero útil para verificar.',
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='1 a 5 estrellas.',
    )
    comment = models.TextField(blank=True, help_text='Comentario opcional.')

    is_published = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'
        ordering = ['-created_at']
        constraints = [
            # Un paciente solo puede tener UNA reseña por doctor (cuando
            # hay patient). Si patient es NULL (anónima), aplicamos dedupe
            # por reviewer_email a nivel app (UniqueConstraint con NULLs
            # no funciona uniformemente entre DBs).
            models.UniqueConstraint(
                fields=['patient', 'doctor'],
                name='unique_review_per_patient_doctor',
                condition=models.Q(patient__isnull=False),
            ),
        ]

    def __str__(self):
        name = self.patient.full_name if self.patient else (self.reviewer_name or 'Anónimo')
        return f'{name} → {self.doctor} ({self.rating}★)'

    @property
    def author_display_name(self) -> str:
        """Nombre a mostrar en la UI. Patient > reviewer_name > 'Anónimo'."""
        if self.patient:
            return self.patient.full_name
        if self.reviewer_name:
            return self.reviewer_name
        return 'Anónimo'


def _default_review_token_expires():
    return timezone.now() + timedelta(days=7)


class PendingReview(models.Model):
    """
    Reseña pendiente de verificación por email.

    Cuando alguien sin cuenta envía una reseña a un doctor, NO la publicamos
    de inmediato — guardamos aquí + mandamos email con un link de
    confirmación. Al hacer click, se promueve a `Review` con is_published=True.

    Esto evita:
      - Reseñas falsas con emails inventados
      - Spam de competidores
      - Que el rating del doctor pueda cambiarse sin trazabilidad
    """
    token = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, db_index=True,
    )
    doctor = models.ForeignKey(
        'catalog.Doctor',
        on_delete=models.CASCADE,
        related_name='pending_reviews',
    )
    reviewer_name = models.CharField(max_length=150)
    reviewer_email = models.EmailField()
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(blank=True)

    expires_at = models.DateTimeField(default=_default_review_token_expires)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_review = models.ForeignKey(
        'Review',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='source_pending',
        help_text='La Review creada al confirmar este pending. Null si aún '
                  'no se ha confirmado.',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reseña pendiente'
        verbose_name_plural = 'Reseñas pendientes'
        ordering = ['-created_at']

    def __str__(self):
        return f'PendingReview({self.reviewer_email} → {self.doctor})'

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_confirmed(self) -> bool:
        return self.confirmed_at is not None
