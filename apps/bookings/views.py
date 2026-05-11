from datetime import date as date_type
import datetime

from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsTenantAdminOrOwner, IsTenantMember
from apps.catalog.models import Doctor, Service
from shared.throttles import BookingCreateThrottle, SlotsThrottle
from shared.viewsets import TenantScopedViewSet

from .models import Appointment, AppointmentStatus
from .serializers import AppointmentCreateSerializer, AppointmentSerializer, SlotSerializer
from .slots import get_available_slots


# ── Public endpoints (no auth) ────────────────────────────────────────────────

class SlotsView(APIView):
    """
    GET /rest/v1/public/slots/?doctor={id}&service={id}&date={YYYY-MM-DD}

    Returns available time slots for the given doctor, service, and date.
    """
    permission_classes = [AllowAny]
    throttle_classes = [SlotsThrottle]

    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'error': 'Tenant requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        doctor_id = request.query_params.get('doctor')
        service_id = request.query_params.get('service')
        date_str = request.query_params.get('date')

        if not all([doctor_id, service_id, date_str]):
            return Response(
                {'error': 'Parámetros requeridos: doctor, service, date.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_date = date_type.fromisoformat(date_str)
        except ValueError:
            return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=400)

        if target_date < date_type.today():
            return Response({'slots': []})

        try:
            doctor = Doctor.objects.for_tenant(tenant).get(pk=doctor_id, is_active=True)
            service = Service.objects.for_tenant(tenant).get(pk=service_id, is_active=True)
        except (Doctor.DoesNotExist, Service.DoesNotExist):
            return Response({'error': 'Doctor o servicio no válido.'}, status=status.HTTP_404_NOT_FOUND)

        slots = get_available_slots(doctor, service, target_date)
        return Response({'slots': slots, 'date': date_str})


class PublicAppointmentCreateView(APIView):
    """
    POST /rest/v1/public/appointments/

    Creates a new appointment. No authentication required.
    """
    permission_classes = [AllowAny]
    throttle_classes = [BookingCreateThrottle]

    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'error': 'Tenant requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AppointmentCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save(tenant=tenant)
        from apps.notifications.tasks import task_send_confirmation
        task_send_confirmation.delay(appointment.pk)
        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)


# ── Admin endpoints (auth required) ──────────────────────────────────────────

class AppointmentViewSet(TenantScopedViewSet):
    """
    CRUD for appointments within the current tenant.
    """
    queryset = Appointment._all.all()
    serializer_class = AppointmentSerializer
    http_method_names = ['get', 'patch', 'delete', 'options', 'head']

    def get_permissions(self):
        # Any tenant member (including doctors) can read AND patch.
        # Backend ensures doctors can only see/modify their own via get_queryset.
        return [IsTenantMember()]

    def get_queryset(self):
        from apps.accounts.models import Membership, MembershipRole
        from apps.catalog.models import Doctor

        qs = Appointment.objects.for_tenant(self.request.tenant).select_related(
            'doctor__user', 'service',
        )

        # If the requester is a doctor, restrict to their own appointments
        membership = Membership.objects.for_tenant(self.request.tenant).filter(
            user=self.request.user, is_active=True,
        ).first()
        if membership and membership.role == MembershipRole.DOCTOR:
            doctor = Doctor.objects.for_tenant(self.request.tenant).filter(user=self.request.user).first()
            if doctor:
                qs = qs.filter(doctor=doctor)
            else:
                return qs.none()

        date_filter = self.request.query_params.get('date')
        doctor_filter = self.request.query_params.get('doctor')
        status_filter = self.request.query_params.get('status')

        if date_filter:
            qs = qs.filter(date=date_filter)
        elif self.request.query_params.get('from_date') or self.request.query_params.get('to_date'):
            from_date = self.request.query_params.get('from_date')
            to_date = self.request.query_params.get('to_date')
            if from_date:
                qs = qs.filter(date__gte=from_date)
            if to_date:
                qs = qs.filter(date__lte=to_date)
        if doctor_filter:
            qs = qs.filter(doctor_id=doctor_filter)
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs
