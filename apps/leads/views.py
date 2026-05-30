from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .emails import send_lead_notifications
from .serializers import LeadCreateSerializer


class LeadThrottle(AnonRateThrottle):
    scope = 'leads'
    rate = '10/hour'


class LeadCreateView(APIView):
    """
    POST /rest/v1/public/leads/

    Público (sin auth). Crea un lead y dispara los dos correos:
    aviso interno + confirmación al prospecto. Rate-limited contra spam.
    """
    permission_classes = [AllowAny]
    throttle_classes = [LeadThrottle]
    authentication_classes = []

    def post(self, request):
        serializer = LeadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead = serializer.save()

        send_lead_notifications(lead)

        return Response(
            {'detail': 'Recibimos tu solicitud. Te contactaremos pronto.'},
            status=status.HTTP_201_CREATED,
        )
