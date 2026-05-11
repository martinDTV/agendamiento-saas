from django.urls import path
from .views import ServiceSuggestView, ChatReplyView

urlpatterns = [
    path('suggest/', ServiceSuggestView.as_view(), name='ai-suggest'),
    path('chat/', ChatReplyView.as_view(), name='ai-chat'),
]
