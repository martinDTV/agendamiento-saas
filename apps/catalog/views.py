from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.accounts.models import Membership, MembershipRole
from apps.accounts.permissions import IsTenantAdminOrOwner, IsTenantMember
from shared.viewsets import TenantScopedViewSet

from .models import Branch, Doctor, Service, Schedule
from .serializers import BranchSerializer, DoctorSerializer, ServiceSerializer, ScheduleSerializer

User = get_user_model()


# ── Public (no auth) ──────────────────────────────────────────────────────────

class PublicDoctorViewSet(viewsets.ReadOnlyModelViewSet):
    """Public read-only list of active doctors for the current tenant.

    Filtros opcionales:
    - ?service=<uuid>: sólo doctores que ofrecen ese servicio.
    """
    serializer_class = DoctorSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if not getattr(self.request, 'tenant', None):
            return Doctor._all.none()
        qs = (
            Doctor.objects.for_tenant(self.request.tenant)
            .filter(is_active=True)
            .select_related('user', 'branch')
            .prefetch_related('services')
        )
        service_id = self.request.query_params.get('service')
        if service_id:
            qs = qs.filter(services__id=service_id, services__is_active=True).distinct()
        return qs


class PublicServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """Public read-only list of active services for the current tenant.

    Filtros opcionales:
    - ?doctor=<uuid>: sólo servicios que ofrece ese doctor.
    """
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if not getattr(self.request, 'tenant', None):
            return Service._all.none()
        qs = (
            Service.objects.for_tenant(self.request.tenant)
            .filter(is_active=True)
            .prefetch_related('doctors')
        )
        doctor_id = self.request.query_params.get('doctor')
        if doctor_id:
            qs = qs.filter(doctors__id=doctor_id, doctors__is_active=True).distinct()
        return qs


class BranchViewSet(TenantScopedViewSet):
    queryset = Branch._all.all()
    serializer_class = BranchSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsTenantMember()]
        return [IsTenantAdminOrOwner()]


class DoctorViewSet(TenantScopedViewSet):
    queryset = Doctor._all.all()
    serializer_class = DoctorSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsTenantMember()]
        return [IsTenantAdminOrOwner()]

    def get_queryset(self):
        return Doctor.objects.for_tenant(self.request.tenant).select_related('user', 'branch')

    @action(detail=False, methods=['get'], permission_classes=[IsTenantMember])
    def me(self, request):
        """GET /catalog/doctors/me/ — current user's doctor profile in this tenant."""
        try:
            doctor = self.get_queryset().get(user=request.user)
            return Response(DoctorSerializer(doctor).data)
        except Doctor.DoesNotExist:
            return Response({'detail': 'No tienes perfil de doctor en este tenant.'}, status=404)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Creates a User + Membership + (optionally) Doctor profile in one call.
        Required: email, password
        Optional: first_name, last_name, role (doctor|admin), specialty, branch, etc.
        """
        data = request.data
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return Response({'detail': 'Email y contraseña son requeridos'}, status=400)

        role = data.get('role', 'doctor')
        if role not in ('doctor', 'admin'):
            return Response({'detail': 'Rol inválido'}, status=400)

        tenant = request.tenant

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': data.get('first_name', ''),
                'last_name':  data.get('last_name', ''),
                'username':   email,
            },
        )
        if created:
            user.set_password(password)
            user.save()

        membership, _ = Membership._all.get_or_create(
            tenant=tenant, user=user,
            defaults={'role': role},
        )

        if role == 'admin':
            return Response({
                'id': str(membership.id),
                'user': user.id,
                'email': user.email,
                'full_name': user.get_full_name() or user.email,
                'role': membership.role,
                'detail': 'Admin creado. Visible en /equipo (no aparece en /doctores).',
            }, status=status.HTTP_201_CREATED)

        existing = Doctor.objects.for_tenant(tenant).filter(user=user).first()
        if existing:
            return Response({'detail': 'Este usuario ya tiene perfil de doctor en esta clínica.'}, status=400)

        branch_id = data.get('branch') or None
        doctor = Doctor._all.create(
            tenant=tenant, user=user,
            branch_id=branch_id,
            specialty=data.get('specialty', ''),
            bio=data.get('bio', ''),
            appointment_duration=data.get('appointment_duration', 30),
            is_active=data.get('is_active', True),
            photo=data.get('photo') or None,
        )
        return Response(DoctorSerializer(doctor).data, status=status.HTTP_201_CREATED)


class ServiceViewSet(TenantScopedViewSet):
    queryset = Service._all.all()
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsTenantMember()]
        return [IsTenantAdminOrOwner()]

    def get_queryset(self):
        return Service.objects.for_tenant(self.request.tenant).prefetch_related('doctors')


class ScheduleViewSet(TenantScopedViewSet):
    queryset = Schedule._all.all()
    serializer_class = ScheduleSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsTenantMember()]
        return [IsTenantAdminOrOwner()]

    def get_queryset(self):
        qs = Schedule.objects.for_tenant(self.request.tenant).select_related('doctor__user')
        doctor_id = self.request.query_params.get('doctor')
        if doctor_id:
            qs = qs.filter(doctor_id=doctor_id)
        return qs
