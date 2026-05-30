from django.db import models


class Lead(models.Model):
    """
    Solicitud de contacto desde la landing de marketing.

    No es un tenant ni un usuario: es un prospecto que dejó sus datos al pedir
    información de un plan. El equipo de NexoSoftDev le da seguimiento manual.
    """
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    plan = models.CharField(
        max_length=50,
        blank=True,
        help_text='Plan que le interesó (gratuito, profesional, clinica, enterprise).',
    )
    message = models.TextField(blank=True)
    source = models.CharField(
        max_length=80,
        default='marketing',
        help_text='De dónde vino el lead (marketing, precios, etc.).',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'leads'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} <{self.email}> — {self.plan or "sin plan"}'
