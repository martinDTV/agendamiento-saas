from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'attachment_url', 'created_at']
        read_only_fields = fields

    def get_attachment_url(self, obj):
        if not obj.attachment:
            return None
        request = self.context.get('request')
        url = obj.attachment.url
        return request.build_absolute_uri(url) if request else url


class ConversationSerializer(serializers.ModelSerializer):
    visitor_display_name = serializers.CharField(read_only=True)
    assigned_agent_name = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField(read_only=True, default=0)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'visitor_name', 'visitor_email', 'visitor_display_name',
            'status', 'assigned_agent', 'assigned_agent_name',
            'started_at', 'assigned_at', 'closed_at', 'last_message_at',
            'unread_count', 'message_count',
        ]
        read_only_fields = fields

    def get_assigned_agent_name(self, obj):
        if not obj.assigned_agent:
            return None
        return obj.assigned_agent.get_full_name() or obj.assigned_agent.email

    def get_message_count(self, obj):
        # Si fue prefetched, usar el cache; si no, contar
        if hasattr(obj, '_prefetched_objects_cache') and 'messages' in obj._prefetched_objects_cache:
            return len(obj.messages.all())
        return obj.messages.count()


class SupportAgentSerializer(serializers.Serializer):
    """Stats por agente de soporte del tenant — no es un modelo, es un agregado."""
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    role = serializers.CharField()
    is_online = serializers.BooleanField()
    total_conversations = serializers.IntegerField()
    open_conversations = serializers.IntegerField()
    closed_conversations = serializers.IntegerField()
    last_active = serializers.DateTimeField(allow_null=True)
    profile_picture_url = serializers.URLField(allow_null=True, required=False)


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['messages']
