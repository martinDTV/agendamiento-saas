from django.db import models

from shared.models import TenantScopedModel, TenantManager, UnscopedManager


class Room(TenantScopedModel):
    """Virtual or physical meeting room scoped to a branch."""

    name = models.CharField(max_length=150)
    branch = models.ForeignKey(
        'catalog.Branch',
        on_delete=models.CASCADE,
        related_name='rooms',
    )
    capacity = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    _all = UnscopedManager()
    objects = TenantManager()

    class Meta(TenantScopedModel.Meta):
        ordering = ['branch__name', 'name']
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'

    def __str__(self):
        return f'{self.name} — {self.branch.name}'


class Meeting(TenantScopedModel):
    """Internal staff meeting (not a patient appointment)."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    organizer = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='organized_meetings',
    )
    participants = models.ManyToManyField(
        'users.User',
        related_name='meetings',
        blank=True,
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='meetings',
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    _all = UnscopedManager()
    objects = TenantManager()

    class Meta(TenantScopedModel.Meta):
        ordering = ['-date', '-start_time']
        verbose_name = 'Junta'
        verbose_name_plural = 'Juntas'

    def __str__(self):
        return f'{self.title} ({self.date})'
