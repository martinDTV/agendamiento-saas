from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AISuggestReplyView,
    ChatAttachmentUploadView,
    SupportAgentViewSet,
    SupportConversationViewSet,
    PublicVisitorMessageView,
)

app_name = 'support'

agent_router = DefaultRouter()
agent_router.register(r'conversations', SupportConversationViewSet, basename='conversation')
agent_router.register(r'agents', SupportAgentViewSet, basename='agent')

public_router = DefaultRouter()
public_router.register(r'conversations', PublicVisitorMessageView, basename='public-conversation')


urlpatterns = [
    # Endpoints autenticados (agentes/admins)
    path('', include(agent_router.urls)),
    path('conversations/<uuid:conversation_id>/ai-suggest-reply/', AISuggestReplyView.as_view(), name='ai-suggest-reply'),
    path('conversations/<uuid:conversation_id>/upload-attachment/', ChatAttachmentUploadView.as_view(), name='upload-attachment'),
    # Subset público (visitantes anónimos pueden leer su propia conversación por id)
    path('public/', include(public_router.urls)),
]
