import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from shared.models import TenantScopedModel, TenantManager, UnscopedManager


class MembershipRole(models.TextChoices):
    OWNER = 'owner', 'Propietario'
    ADMIN = 'admin', 'Administrador'
    DOCTOR = 'doctor', 'Doctor'
    SUPPORT = 'support', 'Soporte'
    STAFF = 'staff', 'Staff'


ROLE_HIERARCHY = {
    MembershipRole.OWNER: 4,
    MembershipRole.ADMIN: 3,
    MembershipRole.DOCTOR: 2,
    MembershipRole.SUPPORT: 2,
    MembershipRole.STAFF: 1,
}


class Membership(TenantScopedModel):
    """Associates a user with a tenant and grants them a role."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    role = models.CharField(max_length=20, choices=MembershipRole.choices)
    is_active = models.BooleanField(default=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_invitations',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    _all = UnscopedManager()
    objects = TenantManager()

    class Meta(TenantScopedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'user'],
                name='unique_user_per_tenant',
            )
        ]
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user.email} @ {self.tenant.slug} [{self.role}]'

    def has_role_at_least(self, role: str) -> bool:
        return ROLE_HIERARCHY.get(self.role, 0) >= ROLE_HIERARCHY.get(role, 0)


def _default_expires():
    return timezone.now() + timedelta(days=7)


class InvitationToken(TenantScopedModel):
    """Magic-link token sent by email to invite a user to a tenant."""

    email = models.EmailField()
    role = models.CharField(max_length=20, choices=MembershipRole.choices, default=MembershipRole.STAFF)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invitations_sent',
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(default=_default_expires)
    created_at = models.DateTimeField(auto_now_add=True)

    _all = UnscopedManager()
    objects = TenantManager()

    class Meta(TenantScopedModel.Meta):
        ordering = ['-created_at']

    def __str__(self):
        return f'Invitation({self.email} → {self.tenant.slug})'

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_accepted(self):
        return self.accepted_at is not None


class UserProfile(models.Model):
    """
    Datos de perfil del usuario que NO viven en el modelo User del paquete `users`.
    Por ahora solo guardamos la foto de perfil; en el futuro podríamos sumar bio,
    timezone, preferencias de notificación, etc.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    def __str__(self):
        return f'Profile<{self.user.email}>'


class PasswordChangeRequired(models.Model):
    """
    Marca usuarios que deben cambiar su contraseña al próximo inicio de sesión.

    Se crea cuando el super admin provisiona un tenant nuevo (la contraseña enviada
    por email es temporal). Se elimina cuando el usuario cambia su contraseña.

    Usar este modelo en lugar de last_login=None porque last_login lo actualiza JWT
    automáticamente al primer login y se perdería el estado.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_change_required',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cambio de contraseña requerido'
        verbose_name_plural = 'Cambios de contraseña requeridos'

    def __str__(self):
        return f'Pending password change for {self.user.email}'
