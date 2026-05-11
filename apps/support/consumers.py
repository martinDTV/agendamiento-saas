"""
WebSocket consumers para el chat soporte.

VisitorConsumer:  /ws/support/visitor/  (público, sin auth)
SupportConsumer:  /ws/support/agent/    (requiere JWT de un usuario con rol soporte/admin/owner)

Wire format de mensajes (JSON):
  Cliente → server:
    { "type": "start", "name": "...", "email": "..." }      visitor only — crea conversación
    { "type": "open", "conversation_id": "..." }            agent only  — abre una conversación
    { "type": "message", "content": "..." }                 ambos       — envía mensaje
    { "type": "close" }                                     agent only  — cierra la conversación
  Server → cliente:
    { "type": "ready", "conversation_id": "...", "status": "open|assigned" }
    { "type": "message", "id": "...", "sender": "visitor|agent|system|ai", "content": "...", "ts": "..." }
    { "type": "status", "status": "...", "agent_name": "..." }
    { "type": "error", "message": "..." }
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from apps.accounts.models import Membership, MembershipRole
from .models import Conversation, ConversationStatus, Message, MessageSender
from .presence import mark_online, mark_offline, online_user_ids


logger = logging.getLogger(__name__)


def _conversation_group(conv_id) -> str:
    return f'conv.{conv_id}'


def _agent_inbox_group(tenant_id) -> str:
    """Canal compartido por todos los agentes de soporte de un tenant — recibe
    notificaciones de nuevas conversaciones que necesitan atención."""
    return f'support.inbox.{tenant_id}'


def _generate_title_async(conv_id):
    """
    Corre en un thread separado: pide a Ollama un título resumen y lo guarda
    en la conversación. Si falla, no rompe nada — el título queda vacío.
    """
    from django.db import connection
    try:
        from apps.ai.ollama import summarize_conversation_title
        messages = list(
            Message.objects.filter(conversation_id=conv_id)
            .order_by('created_at')
            .values('sender', 'content')
        )
        title = summarize_conversation_title(messages)
        if title:
            Conversation._all.filter(pk=conv_id).update(title=title)
            logger.info('Generated title for conv=%s: %s', conv_id, title[:60])
    except Exception as exc:
        logger.warning('Background title generation failed for conv=%s: %s', conv_id, exc)
    finally:
        # Cerrar la conexión a DB del thread (no se cierra sola en threads ad-hoc)
        connection.close()


class VisitorConsumer(AsyncJsonWebsocketConsumer):
    """Visitante público — abre conversación, manda mensajes, recibe respuestas."""

    async def connect(self):
        tenant = self.scope.get('tenant')
        logger.info('VisitorConsumer.connect tenant=%r origin=%r', tenant, self.scope.get('origin'))
        if not tenant:
            logger.warning('VisitorConsumer rejected: no tenant in scope')
            await self.close(code=4003)
            return
        self.tenant = tenant
        self.conversation_id = None
        self.group_name = None
        await self.accept()
        logger.info('VisitorConsumer accepted for tenant=%s', tenant.slug)

    async def disconnect(self, code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        msg_type = content.get('type')
        logger.warning('VisitorConsumer.receive type=%s conv=%s', msg_type, self.conversation_id)

        if msg_type == 'start':
            await self._handle_start(content)
        elif msg_type == 'message':
            await self._handle_message(content)
        elif msg_type == 'close':
            await self._handle_close()
        else:
            await self.send_json({'type': 'error', 'message': f'Tipo de mensaje desconocido: {msg_type}'})

    async def _handle_close(self):
        if not self.conversation_id or not self.group_name:
            return
        logger.warning('Visitor closing conv=%s', self.conversation_id)
        await self._close_conversation_db(self.conversation_id)
        # Avisar a todos los presentes (el agente) que el visitante cerró
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat.status',
                'status': 'closed',
                'closed_by': 'visitor',
            },
        )

    @database_sync_to_async
    def _close_conversation_db(self, conv_id):
        from django.utils import timezone as djtz
        Conversation._all.filter(pk=conv_id).update(
            status=ConversationStatus.CLOSED,
            closed_at=djtz.now(),
        )
        import threading
        threading.Thread(
            target=_generate_title_async,
            args=(conv_id,),
            daemon=True,
        ).start()

    async def _handle_start(self, content):
        if self.conversation_id:
            return
        name = (content.get('name') or '').strip()[:120]
        email = (content.get('email') or '').strip()[:254]
        conv = await self._create_conversation(name, email)
        self.conversation_id = str(conv.id)
        self.group_name = _conversation_group(self.conversation_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Notificar a agentes online del tenant que hay una nueva conversación
        await self.channel_layer.group_send(
            _agent_inbox_group(self.tenant.id),
            {
                'type': 'inbox.new_conversation',
                'conversation_id': self.conversation_id,
                'visitor_name': conv.visitor_display_name,
                'started_at': conv.started_at.isoformat(),
            },
        )

        await self.send_json({
            'type': 'ready',
            'conversation_id': self.conversation_id,
            'status': conv.status,
        })

        # Mensaje de sistema inicial
        agents = online_user_ids(self.tenant.id)
        if agents:
            text = 'Conectándote con un agente disponible…'
        else:
            text = 'Por ahora no hay agentes en línea. Tu mensaje se va a guardar y un agente te responderá pronto.'
        await self._post_message(MessageSender.SYSTEM, text)

    async def _handle_message(self, content):
        if not self.conversation_id:
            await self.send_json({'type': 'error', 'message': 'Iniciá una conversación primero.'})
            return
        text = (content.get('content') or '').strip()
        if not text:
            return
        await self._post_message(MessageSender.VISITOR, text)

    async def _post_message(self, sender, text):
        msg = await self._save_message(sender, text)
        logger.warning(
            'Visitor posting message conv=%s sender=%s group=%s text=%r',
            self.conversation_id, sender, self.group_name, text[:60]
        )
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat.message',
                'id': str(msg.id),
                'sender': msg.sender,
                'content': msg.content,
                'ts': msg.created_at.isoformat(),
            },
        )

    # ── handlers de canal (group_send dispatches aquí) ──

    async def chat_message(self, event):
        await self.send_json({
            'type': 'message',
            'id': event['id'],
            'sender': event['sender'],
            'content': event['content'],
            'attachment_url': event.get('attachment_url'),
            'ts': event['ts'],
        })

    async def chat_status(self, event):
        await self.send_json({
            'type': 'status',
            'status': event['status'],
            'agent_name': event.get('agent_name'),
            'agent_avatar_url': event.get('agent_avatar_url'),
            'closed_by': event.get('closed_by'),
        })

    # ── DB helpers ──

    @database_sync_to_async
    def _create_conversation(self, name, email):
        return Conversation._all.create(
            tenant=self.tenant,
            visitor_name=name,
            visitor_email=email,
            status=ConversationStatus.OPEN,
        )

    @database_sync_to_async
    def _save_message(self, sender, content):
        from django.utils import timezone as djtz
        msg = Message.objects.create(
            conversation_id=uuid.UUID(self.conversation_id),
            sender=sender,
            content=content,
        )
        Conversation._all.filter(pk=msg.conversation_id).update(last_message_at=djtz.now())
        return msg


class SupportConsumer(AsyncJsonWebsocketConsumer):
    """Agente de soporte autenticado."""

    async def connect(self):
        user = self.scope.get('user')
        tenant = self.scope.get('tenant')
        logger.info(
            'SupportConsumer.connect user=%r tenant=%r origin=%r',
            getattr(user, 'email', None), tenant, self.scope.get('origin')
        )
        if user is None or isinstance(user, AnonymousUser):
            logger.warning('SupportConsumer rejected: anonymous or missing user')
            await self.close(code=4003)
            return
        if not tenant:
            logger.warning('SupportConsumer rejected: no tenant in scope')
            await self.close(code=4003)
            return
        if not await self._is_support_user(user, tenant):
            logger.warning('SupportConsumer rejected: user %s not a support agent of %s', user.email, tenant.slug)
            await self.close(code=4003)
            return

        self.user = user
        self.tenant = tenant
        self.inbox_group = _agent_inbox_group(tenant.id)
        self.conversation_id = None
        self.conv_group = None

        await self.channel_layer.group_add(self.inbox_group, self.channel_name)
        mark_online(tenant.id, user.pk)
        await self.accept()
        await self.send_json({'type': 'ready'})

    async def disconnect(self, code):
        if hasattr(self, 'inbox_group'):
            await self.channel_layer.group_discard(self.inbox_group, self.channel_name)
        if self.conv_group:
            await self.channel_layer.group_discard(self.conv_group, self.channel_name)
        if hasattr(self, 'tenant') and hasattr(self, 'user'):
            mark_offline(self.tenant.id, self.user.pk)

    async def receive_json(self, content, **kwargs):
        msg_type = content.get('type')
        logger.warning(
            'SupportConsumer.receive type=%s conv=%s user=%s',
            msg_type, self.conversation_id, getattr(self.user, 'email', None)
        )

        if msg_type == 'open':
            await self._handle_open(content)
        elif msg_type == 'message':
            await self._handle_message(content)
        elif msg_type == 'close':
            await self._handle_close()
        else:
            await self.send_json({'type': 'error', 'message': f'Tipo de mensaje desconocido: {msg_type}'})

    async def _handle_open(self, content):
        conv_id = content.get('conversation_id')
        if not conv_id:
            return
        conv = await self._assign_conversation(conv_id)
        if not conv:
            logger.warning('Agent tried to open conv=%s but it was rejected (closed or not found)', conv_id)
            await self.send_json({'type': 'error', 'message': 'Conversación no encontrada o ya cerrada.'})
            return

        # Salir del grupo anterior si lo había
        if self.conv_group:
            await self.channel_layer.group_discard(self.conv_group, self.channel_name)
        self.conversation_id = str(conv.id)
        self.conv_group = _conversation_group(self.conversation_id)
        await self.channel_layer.group_add(self.conv_group, self.channel_name)
        logger.warning(
            'Agent %s joined conv group=%s (visitor=%s status=%s)',
            self.user.email, self.conv_group, conv.visitor_display_name, conv.status
        )

        # Avisar al canal que se asignó (visitante recibe el cambio de status)
        agent_avatar = await self._get_agent_avatar_url()
        await self.channel_layer.group_send(
            self.conv_group,
            {
                'type': 'chat.status',
                'status': 'assigned',
                'agent_name': self.user.get_full_name() or self.user.email,
                'agent_avatar_url': agent_avatar,
            },
        )

        # Mensaje sistema: "Hola {visitor_name}, te atiende {agent_name}"
        greeting = (
            f'Hola {conv.visitor_display_name}. Te atiende '
            f'{self.user.get_full_name() or self.user.email}. ¿En qué te puedo ayudar?'
        )
        msg = await self._save_system_message(conv.id, greeting)
        await self.channel_layer.group_send(
            self.conv_group,
            {
                'type': 'chat.message',
                'id': str(msg.id),
                'sender': msg.sender,
                'content': msg.content,
                'ts': msg.created_at.isoformat(),
            },
        )

        await self.send_json({
            'type': 'opened',
            'conversation_id': self.conversation_id,
            'visitor_name': conv.visitor_display_name,
        })

    async def _handle_message(self, content):
        if not self.conv_group:
            logger.warning('Agent tried to send message but no conv_group active (forgot to open?)')
            await self.send_json({'type': 'error', 'message': 'Abrí una conversación primero.'})
            return
        text = (content.get('content') or '').strip()
        if not text:
            return
        msg = await self._save_agent_message(self.conversation_id, text)
        logger.warning(
            'Agent posting message conv=%s group=%s text=%r',
            self.conversation_id, self.conv_group, text[:60]
        )
        await self.channel_layer.group_send(
            self.conv_group,
            {
                'type': 'chat.message',
                'id': str(msg.id),
                'sender': msg.sender,
                'content': msg.content,
                'ts': msg.created_at.isoformat(),
            },
        )

    async def _handle_close(self):
        if not self.conversation_id:
            return
        logger.warning('Agent %s closing conv=%s', self.user.email, self.conversation_id)
        await self._close_conversation(self.conversation_id)
        await self.channel_layer.group_send(
            self.conv_group,
            {
                'type': 'chat.status',
                'status': 'closed',
                'closed_by': 'agent',
            },
        )
        await self.channel_layer.group_discard(self.conv_group, self.channel_name)
        self.conv_group = None
        self.conversation_id = None

    # ── handlers de canal ──

    async def chat_message(self, event):
        await self.send_json({
            'type': 'message',
            'id': event['id'],
            'sender': event['sender'],
            'content': event['content'],
            'attachment_url': event.get('attachment_url'),
            'ts': event['ts'],
        })

    async def chat_status(self, event):
        await self.send_json({
            'type': 'status',
            'status': event['status'],
            'agent_name': event.get('agent_name'),
            'closed_by': event.get('closed_by'),
        })

    async def inbox_new_conversation(self, event):
        await self.send_json({
            'type': 'inbox',
            'event': 'new_conversation',
            'conversation_id': event['conversation_id'],
            'visitor_name': event['visitor_name'],
            'started_at': event['started_at'],
        })

    # ── DB helpers ──

    @database_sync_to_async
    def _get_agent_avatar_url(self):
        profile = getattr(self.user, 'profile', None)
        if not profile or not profile.profile_picture:
            return None
        # Construir URL absoluta usando el host configurado.
        # Si MEDIA_URL es relativo, anteponemos algún base. En dev daphne sirve desde 8000.
        from django.conf import settings as djs
        base = getattr(djs, 'MEDIA_BASE_URL', 'http://localhost:8000')
        return f'{base.rstrip("/")}{profile.profile_picture.url}'

    @database_sync_to_async
    def _is_support_user(self, user, tenant):
        return Membership._all.filter(
            tenant=tenant,
            user=user,
            is_active=True,
            role__in=[MembershipRole.OWNER, MembershipRole.ADMIN, MembershipRole.SUPPORT],
        ).exists()

    @database_sync_to_async
    def _assign_conversation(self, conv_id):
        from django.utils import timezone as djtz
        try:
            conv = Conversation._all.select_related('tenant').get(
                pk=conv_id, tenant=self.tenant,
            )
        except (Conversation.DoesNotExist, ValueError):
            return None
        if conv.status == ConversationStatus.CLOSED:
            return None
        conv.status = ConversationStatus.ASSIGNED
        conv.assigned_agent = self.user
        conv.assigned_at = djtz.now()
        conv.save(update_fields=['status', 'assigned_agent', 'assigned_at'])
        return conv

    @database_sync_to_async
    def _save_agent_message(self, conv_id, content):
        from django.utils import timezone as djtz
        msg = Message.objects.create(
            conversation_id=uuid.UUID(conv_id),
            sender=MessageSender.AGENT,
            sender_user=self.user,
            content=content,
        )
        Conversation._all.filter(pk=msg.conversation_id).update(last_message_at=djtz.now())
        return msg

    @database_sync_to_async
    def _save_system_message(self, conv_id, content):
        from django.utils import timezone as djtz
        msg = Message.objects.create(
            conversation_id=conv_id,
            sender=MessageSender.SYSTEM,
            content=content,
        )
        Conversation._all.filter(pk=msg.conversation_id).update(last_message_at=djtz.now())
        return msg

    @database_sync_to_async
    def _close_conversation(self, conv_id):
        """
        Cierra la conversación INMEDIATAMENTE (sin esperar a la IA). El título
        resumen se genera en background después, así no bloqueamos el broadcast
        del 'chat.status' al visitante.
        """
        from django.utils import timezone as djtz
        Conversation._all.filter(pk=conv_id).update(
            status=ConversationStatus.CLOSED,
            closed_at=djtz.now(),
        )
        # Disparar generación del título en un thread separado (best-effort).
        import threading
        threading.Thread(
            target=_generate_title_async,
            args=(conv_id,),
            daemon=True,
        ).start()
