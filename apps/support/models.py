import uuid

from django.conf import settings
from django.db import models

from shared.models import TenantScopedModel, TenantManager, UnscopedManager


class ConversationStatus(models.TextChoices):
    OPEN = 'open', 'Abierta (esperando agente)'
    ASSIGNED = 'assigned', 'Asignada'
    CLOSED = 'closed', 'Cerrada'


class Conversation(TenantScopedModel):
    """
    Una sesión de chat entre un visitante (paciente público) y un agente de soporte.

    Una conversación arranca como `open` cuando el visitante apreta "Hablar con
    humano" en la burbuja del chat público. Luego un usuario con rol soporte
    online la levanta → pasa a `assigned`. Al cerrar pasa a `closed`.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Datos del visitante (no autenticado — pueden ser anónimos)
    visitor_name = models.CharField(max_length=120, blank=True, default='')
    visitor_email = models.EmailField(blank=True, default='')

    status = models.CharField(
        max_length=16,
        choices=ConversationStatus.choices,
        default=ConversationStatus.OPEN,
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='support_conversations',
    )

    title = models.CharField(
        max_length=120,
        blank=True,
        default='',
        help_text='Resumen corto de la conversación, generado por IA al cerrar.',
    )

    started_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    _all = UnscopedManager()
    objects = TenantManager()

    class Meta(TenantScopedModel.Meta):
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['tenant', 'status', '-started_at']),
        ]

    def __str__(self):
        return f'Conversation({self.id} · {self.tenant.slug} · {self.status})'

    @property
    def visitor_display_name(self) -> str:
        return self.visitor_name or self.visitor_email or 'Visitante anónimo'


class MessageSender(models.TextChoices):
    VISITOR = 'visitor', 'Visitante'
    AGENT = 'agent', 'Agente'
    SYSTEM = 'system', 'Sistema'
    AI = 'ai', 'IA'


class Message(models.Model):
    """Mensaje individual dentro de una conversación."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.CharField(max_length=12, choices=MessageSender.choices)
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='Solo para sender=agent',
    )
    content = models.TextField(blank=True, default='')
    attachment = models.ImageField(upload_to='chat_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f'Message({self.sender} · {self.created_at:%H:%M})'
