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

    Tenant resolution (cross-clínica friendly):
      1. Si `request.tenant` viene del middleware (Host o X-Tenant-Slug) y el
         doctor pertenece a ese tenant → se usa.
      2. Si NO viene tenant → el tenant se deduce del `doctor` enviado. Esto
         permite que la app móvil llame el endpoint sin saber a qué clínica
         pertenece el doctor.
      3. Si hay tenant pero el doctor pertenece a OTRO tenant → 404 (mismatch).
    """
    permission_classes = [AllowAny]
    throttle_classes = [SlotsThrottle]

    def get(self, request):
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

        # Resolvemos doctor primero usando el manager unscoped — el tenant
        # se deduce de ahí si hace falta. Validamos que tanto doctor como
        # service estén activos y pertenezcan al mismo tenant.
        try:
            doctor = (
                Doctor._all
                .select_related('tenant')
                .get(pk=doctor_id, is_active=True, tenant__is_active=True)
            )
        except (Doctor.DoesNotExist, ValueError):
            return Response({'error': 'Doctor no válido.'}, status=status.HTTP_404_NOT_FOUND)

        tenant_from_header = getattr(request, 'tenant', None)
        if tenant_from_header and tenant_from_header.id != doctor.tenant_id:
            # Mismatch: el header dice una clínica, el doctor pertenece a otra.
            # Tratamos como "doctor no válido en este contexto" — seguridad.
            return Response({'error': 'Doctor no válido.'}, status=status.HTTP_404_NOT_FOUND)

        tenant = doctor.tenant

        try:
            service = Service._all.get(
                pk=service_id, is_active=True, tenant=tenant,
            )
        except (Service.DoesNotExist, ValueError):
            return Response(
                {'error': 'Servicio no válido para este doctor.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        slots = get_available_slots(doctor, service, target_date)
        return Response({'slots': slots, 'date': date_str})


class PublicAppointmentCreateView(APIView):
    """
    POST /rest/v1/public/appointments/

    Creates a new appointment.

    No requiere autenticación. PERO: si el request trae JWT válido y el user
    tiene un Patient asociado, vinculamos automáticamente `appointment.patient`
    para que aparezca en `/patients/me/appointments/`.

    Si el paciente está autenticado, también pre-llenamos los campos
    patient_name/email/phone con sus datos del perfil cuando no vienen en la
    request (la app móvil los manda igual, pero esto previene mismatches).
    """
    permission_classes = [AllowAny]
    throttle_classes = [BookingCreateThrottle]

    def post(self, request):
        # Tenant resolution cross-clínica (mismo patrón que SlotsView):
        # si no viene del middleware, lo deducimos del doctor enviado.
        doctor_id = request.data.get('doctor')
        if not doctor_id:
            return Response(
                {'doctor': ['Este campo es requerido.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            doctor = (
                Doctor._all
                .select_related('tenant')
                .get(pk=doctor_id, is_active=True, tenant__is_active=True)
            )
        except (Doctor.DoesNotExist, ValueError, TypeError):
            return Response({'doctor': ['Doctor no válido.']}, status=status.HTTP_400_BAD_REQUEST)

        tenant_from_header = getattr(request, 'tenant', None)
        if tenant_from_header and tenant_from_header.id != doctor.tenant_id:
            return Response({'doctor': ['Doctor no válido.']}, status=status.HTTP_400_BAD_REQUEST)

        tenant = doctor.tenant
        # `request.tenant` lo necesita el AppointmentCreateSerializer.validate()
        # para verificar que doctor/service son del mismo tenant. Lo seteamos
        # explícitamente para que el contexto funcione.
        request.tenant = tenant

        # Si el request está autenticado, intentamos resolver el Patient.
        # Importamos aquí para evitar import circular bookings ↔ patients.
        patient = None
        if request.user and request.user.is_authenticated:
            from apps.patients.models import Patient
            patient = Patient.objects.filter(user=request.user).first()

        serializer = AppointmentCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        save_kwargs = {'tenant': tenant}
        if patient is not None:
            save_kwargs['patient'] = patient
        appointment = serializer.save(**save_kwargs)
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

        # Free-text search by patient contact (name / email / phone). Useful when
        # a patient calls to reschedule and the agent searches by their details.
        search = (self.request.query_params.get('search') or '').strip()
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(patient_name__icontains=search)
                | Q(patient_email__icontains=search)
                | Q(patient_phone__icontains=search)
            )

        return qs
