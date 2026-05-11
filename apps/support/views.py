from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Max
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Membership, MembershipRole

from .models import Conversation, ConversationStatus, Message, MessageSender
from .permissions import IsSupportAgent
from .presence import online_user_ids
from .serializers import (
    ConversationSerializer,
    ConversationDetailSerializer,
    MessageSerializer,
    SupportAgentSerializer,
)


User = get_user_model()


class SupportConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only para agentes/admins. La asignación y cierre se hacen vía WS,
    pero exponemos endpoints REST para listar y ver historial.
    """
    permission_classes = [IsSupportAgent]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        qs = (
            Conversation.objects.for_tenant(self.request.tenant)
            .select_related('assigned_agent')
            .prefetch_related('messages')
        )
        status_filter = self.request.query_params.get('status')
        if status_filter in dict(ConversationStatus.choices):
            qs = qs.filter(status=status_filter)
        agent_id = self.request.query_params.get('agent')
        if agent_id:
            qs = qs.filter(assigned_agent_id=agent_id)
        return qs.order_by('-last_message_at', '-started_at')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = Conversation.objects.for_tenant(request.tenant)
        return Response({
            'open': qs.filter(status=ConversationStatus.OPEN).count(),
            'assigned': qs.filter(status=ConversationStatus.ASSIGNED).count(),
            'closed': qs.filter(status=ConversationStatus.CLOSED).count(),
            'agents_online': len(online_user_ids(request.tenant.id)),
        })


class SupportAgentViewSet(viewsets.ViewSet):
    """
    Lista de agentes de soporte del tenant con stats agregadas:
    - total de conversaciones atendidas
    - abiertas / cerradas
    - estado online (vía Redis)
    - última actividad
    """
    permission_classes = [IsSupportAgent]

    def list(self, request):
        # Memberships con rol que puede atender soporte
        eligible_roles = [MembershipRole.OWNER, MembershipRole.ADMIN, MembershipRole.SUPPORT]
        members = (
            Membership._all.filter(
                tenant=request.tenant,
                is_active=True,
                role__in=eligible_roles,
            )
            .select_related('user')
        )

        online_set = set(online_user_ids(request.tenant.id))

        # Agregados de Conversation por assigned_agent
        agg = (
            Conversation._all.filter(tenant=request.tenant, assigned_agent__isnull=False)
            .values('assigned_agent_id')
            .annotate(
                total=Count('id'),
                open_count=Count('id', filter=~Q(status=ConversationStatus.CLOSED)),
                closed_count=Count('id', filter=Q(status=ConversationStatus.CLOSED)),
                last_active=Max('last_message_at'),
            )
        )
        stats_by_user = {row['assigned_agent_id']: row for row in agg}

        out = []
        for m in members:
            stats = stats_by_user.get(m.user_id, {})
            profile = getattr(m.user, 'profile', None)
            pic_url = None
            if profile and profile.profile_picture:
                pic_url = request.build_absolute_uri(profile.profile_picture.url)
            out.append({
                'user_id': m.user_id,
                'email': m.user.email,
                'full_name': m.user.get_full_name() or m.user.email,
                'role': m.role,
                'is_online': m.user_id in online_set,
                'total_conversations': stats.get('total', 0),
                'open_conversations': stats.get('open_count', 0),
                'closed_conversations': stats.get('closed_count', 0),
                'last_active': stats.get('last_active'),
                'profile_picture_url': pic_url,
            })

        # Ordenar: online primero, luego por última actividad
        out.sort(key=lambda x: (not x['is_online'], -(x['total_conversations'] or 0)))
        return Response(SupportAgentSerializer(out, many=True).data)


class ChatAttachmentUploadView(APIView):
    """
    POST /rest/v1/support/conversations/{id}/upload-attachment/
    Sube una imagen y la asocia al chat. Devuelve la URL para mandar por WS.
    Acepta tanto agentes (autenticados) como visitantes (público) — el visitante
    debe estar conectado al WS de su conversación, validamos que la conv existe.
    """
    permission_classes = [AllowAny]

    def post(self, request, conversation_id=None):
        try:
            conv = Conversation._all.get(pk=conversation_id)
        except (Conversation.DoesNotExist, ValueError):
            return Response({'detail': 'Conversación no encontrada.'}, status=404)
        if conv.status == ConversationStatus.CLOSED:
            return Response({'detail': 'La conversación está cerrada.'}, status=409)

        image = request.FILES.get('image')
        if not image:
            return Response({'detail': 'Subí un archivo en el campo "image".'}, status=400)
        if image.size > 10 * 1024 * 1024:  # 10MB max
            return Response({'detail': 'La imagen no puede pesar más de 10 MB.'}, status=400)

        sender = request.data.get('sender') or 'visitor'
        if sender not in ('visitor', 'agent'):
            return Response({'detail': 'sender inválido.'}, status=400)

        sender_user = request.user if (sender == 'agent' and request.user.is_authenticated) else None

        msg = Message.objects.create(
            conversation=conv,
            sender=sender,
            sender_user=sender_user,
            content='',
            attachment=image,
        )
        from django.utils import timezone as djtz
        Conversation._all.filter(pk=conv.pk).update(last_message_at=djtz.now())

        url = request.build_absolute_uri(msg.attachment.url) if msg.attachment else None

        # Broadcast a la conversación así ambos lados (visitante + agente) reciben
        # el mensaje con la imagen en tiempo real.
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        layer = get_channel_layer()
        if layer is not None:
            async_to_sync(layer.group_send)(
                f'conv.{conv.pk}',
                {
                    'type': 'chat.message',
                    'id': str(msg.id),
                    'sender': msg.sender,
                    'content': '',
                    'attachment_url': url,
                    'ts': msg.created_at.isoformat(),
                },
            )

        return Response({
            'id': str(msg.id),
            'sender': msg.sender,
            'content': '',
            'attachment_url': url,
            'ts': msg.created_at.isoformat(),
        })


class AISuggestReplyView(APIView):
    """
    POST /rest/v1/support/conversations/{id}/ai-suggest-reply/
    Devuelve un draft de respuesta sugerida por IA para que el agente la edite y envíe.
    Solo agentes/admins/owners.
    """
    permission_classes = [IsSupportAgent]

    def post(self, request, conversation_id=None):
        from apps.ai.ollama import suggest_agent_reply
        from apps.catalog.models import Doctor, Service

        try:
            conv = Conversation.objects.for_tenant(request.tenant).get(pk=conversation_id)
        except (Conversation.DoesNotExist, ValueError):
            return Response({'detail': 'Conversación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        history = list(conv.messages.order_by('created_at').values('sender', 'content'))
        if not history:
            return Response({'reply': ''})

        services_payload = [
            {'name': s['name'], 'duration': s['duration'], 'price': str(s['price'])}
            for s in Service.objects.for_tenant(request.tenant).filter(is_active=True).values('name', 'duration', 'price')
        ]
        doctors_payload = [
            {
                'name': d.user.get_full_name() or d.user.email,
                'specialty': d.specialty or '',
            }
            for d in Doctor.objects.for_tenant(request.tenant).filter(is_active=True).select_related('user')
        ]

        ctx = {
            'name': request.tenant.name,
            'services': services_payload,
            'doctors': doctors_payload,
        }

        reply = suggest_agent_reply(history, ctx)
        return Response({'reply': reply})


class PublicVisitorMessageView(viewsets.GenericViewSet):
    """
    Endpoints para que el visitante público pueda recuperar el estado de su
    conversación sin necesidad del WebSocket (ej. al recargar la página).
    """
    permission_classes = [AllowAny]
    serializer_class = MessageSerializer

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        try:
            conv = Conversation._all.get(pk=pk)
        except (Conversation.DoesNotExist, ValueError):
            return Response({'detail': 'Conversación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        if request.tenant and conv.tenant_id != request.tenant.id:
            return Response({'detail': 'Conversación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        msgs = conv.messages.order_by('created_at')
        return Response({
            'conversation_id': str(conv.id),
            'status': conv.status,
            'messages': MessageSerializer(msgs, many=True).data,
        })
