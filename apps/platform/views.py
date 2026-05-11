import logging
import re

from django.conf import settings as django_settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.db import transaction
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.utils.crypto import get_random_string

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Membership, MembershipRole, InvitationToken, PasswordChangeRequired
from apps.tenants.models import Tenant

from .models import Plan, Subscription, Discount, SubscriptionStatus, PlatformSettings
from .permissions import IsPlatformAdmin
from .serializers import (
    PlanSerializer,
    DiscountSerializer,
    SubscriptionSerializer,
    TenantPlatformSerializer,
    PlatformSettingsSerializer,
)


User = get_user_model()
logger = logging.getLogger(__name__)


def _generate_admin_password() -> str:
    """Strong-ish random password for new tenant admins; user is forced to change later."""
    return get_random_string(12, allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#%')


# ── Auth ──────────────────────────────────────────────────────────────────────

class PlatformLoginView(APIView):
    """
    POST /rest/v1/platform/auth/login/
    Solo permite login a superusuarios. Rechaza usuarios de tenant.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''

        if not email or not password:
            return Response(
                {'error': 'Email y contraseña son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response(
                {'error': 'Credenciales inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {'error': 'Cuenta inactiva.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not user.is_superuser:
            return Response(
                {'error': 'No tienes acceso a la plataforma.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.get_full_name() or user.email,
                'is_superuser': True,
            },
        }, status=status.HTTP_200_OK)


class PlatformMeView(APIView):
    """GET /rest/v1/platform/auth/me/ — datos del platform admin actual."""
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        u = request.user
        return Response({
            'id': u.id,
            'email': u.email,
            'full_name': u.get_full_name() or u.email,
            'is_superuser': True,
        })


# ── Dashboard ─────────────────────────────────────────────────────────────────

class PlatformDashboardView(APIView):
    """GET /rest/v1/platform/dashboard/ — KPIs globales."""
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        total_tenants = Tenant.objects.count()
        active_tenants = Tenant.objects.filter(is_active=True).count()

        subs = Subscription.objects.select_related('plan', 'discount')
        active_subs = subs.filter(status=SubscriptionStatus.ACTIVE).count()
        trial_subs = subs.filter(status=SubscriptionStatus.TRIAL).count()
        canceled_subs = subs.filter(status=SubscriptionStatus.CANCELED).count()

        # MRR (suma de price_monthly de todas las suscripciones activas)
        mrr = sum(
            float(s.plan.price_monthly)
            for s in subs.filter(status=SubscriptionStatus.ACTIVE)
        )

        # Distribución por plan
        plan_dist = (
            Plan.objects.annotate(active_subs=Count(
                'subscriptions',
                filter=Q(subscriptions__status=SubscriptionStatus.ACTIVE),
            ))
            .values('id', 'name', 'price_monthly', 'active_subs')
        )

        return Response({
            'tenants': {
                'total': total_tenants,
                'active': active_tenants,
                'inactive': total_tenants - active_tenants,
            },
            'subscriptions': {
                'active': active_subs,
                'trial': trial_subs,
                'canceled': canceled_subs,
                'total': subs.count(),
            },
            'revenue': {
                'mrr': round(mrr, 2),
                'arr': round(mrr * 12, 2),
                'currency': 'MXN',
            },
            'plans': list(plan_dist),
        })


# ── Tenants ───────────────────────────────────────────────────────────────────

class PlatformTenantViewSet(viewsets.ModelViewSet):
    """CRUD global de tenants — solo platform admins."""
    queryset = Tenant.objects.all().select_related('subscription__plan', 'subscription__discount')
    serializer_class = TenantPlatformSerializer
    permission_classes = [IsPlatformAdmin]
    lookup_field = 'pk'

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q))
        is_active = self.request.query_params.get('is_active')
        if is_active in ('true', 'false'):
            qs = qs.filter(is_active=(is_active == 'true'))
        return qs

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Provisiona un tenant nuevo en una sola operación atómica:
        1. Crea Tenant (plan='free' por defecto, is_active=True)
        2. Crea User admin (is_active=False — debe activar por email)
        3. Crea Membership(role=OWNER) ligando user ↔ tenant
        4. Crea InvitationToken para activación
        5. Envía email con: contraseña temporal + link de activación

        Body: { name, slug, type, admin_email, admin_first_name, admin_last_name }
        """
        data = request.data
        name = (data.get('name') or '').strip()
        slug = (data.get('slug') or '').strip().lower()
        tenant_type = (data.get('type') or 'clinic').strip()
        admin_email = (data.get('admin_email') or '').strip().lower()
        admin_first = (data.get('admin_first_name') or '').strip()
        admin_last = (data.get('admin_last_name') or '').strip()

        if not name or not slug or not admin_email:
            return Response(
                {'detail': 'name, slug y admin_email son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not re.fullmatch(r'[a-z0-9-]+', slug):
            return Response(
                {'detail': 'El slug solo permite letras minúsculas, números y guiones.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if Tenant.objects.filter(slug=slug).exists():
            return Response({'detail': 'Ya existe un tenant con ese slug.'}, status=status.HTTP_409_CONFLICT)
        if User.objects.filter(email=admin_email).exists():
            return Response(
                {'detail': 'Ya existe un usuario con ese email. Usa el flujo de invitación en lugar de crear tenant.'},
                status=status.HTTP_409_CONFLICT,
            )

        tenant = Tenant.objects.create(
            slug=slug,
            name=name,
            type=tenant_type,
            plan='free',
            is_active=True,
        )

        password = _generate_admin_password()
        user = User.objects.create_user(
            email=admin_email,
            password=password,
            first_name=admin_first,
            last_name=admin_last,
            username=admin_email,
        )
        # Cuenta inactiva hasta que el admin haga click en el link de activación.
        user.is_active = False
        user.save(update_fields=['is_active'])

        Membership._all.create(
            tenant=tenant,
            user=user,
            role=MembershipRole.OWNER,
        )

        invitation = InvitationToken._all.create(
            tenant=tenant,
            email=admin_email,
            role=MembershipRole.OWNER,
            invited_by=request.user,
        )

        # Forzar cambio de contraseña al primer login (la del email es temporal)
        PasswordChangeRequired.objects.create(user=user)

        self._send_activation_email(tenant, user, invitation, password)

        serializer = self.get_serializer(tenant)
        return Response(
            {**serializer.data, 'admin_email': admin_email, 'email_sent': True},
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _send_activation_email(tenant: Tenant, user, invitation: InvitationToken, password: str):
        from shared.colors import darken, normalize_hex

        # Plantilla del URL del admin por tenant — configurable vía env.
        # Ej: 'http://admin.{slug}.miapp.com:3002' → en prod 'https://admin.{slug}.miapp.com'
        template = getattr(django_settings, 'ADMIN_BASE_URL_TEMPLATE', 'http://admin.{slug}.miapp.com:3002')
        admin_base = template.format(slug=tenant.slug)
        activation_url = f'{admin_base}/activate/{invitation.token}'

        # Nombre de la plataforma — leído desde settings singleton; fallback al hostname.
        try:
            platform_settings = PlatformSettings.get_solo()
            platform_name = platform_settings.platform_name or 'Agendamiento SaaS'
        except Exception:
            platform_name = 'Agendamiento SaaS'

        # Color del tenant (definido en su branding) — fallback al sage default.
        tenant_color = (tenant.settings or {}).get('branding', {}).get('primaryColor') or '#6FA776'
        primary_color = normalize_hex(tenant_color, fallback='#6FA776')
        primary_color_dark = darken(primary_color, amount=0.18)

        ctx = {
            'tenant_name': tenant.name,
            'tenant_slug': tenant.slug,
            'first_name': user.first_name,
            'email': user.email,
            'password': password,
            'activation_url': activation_url,
            'platform_name': platform_name,
            'primary_color': primary_color,
            'primary_color_dark': primary_color_dark,
        }

        subject = f'Activa tu cuenta de {tenant.name}'
        text_body = render_to_string('platform/emails/tenant_activation.txt', ctx)
        html_body = render_to_string('platform/emails/tenant_activation.html', ctx)

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=None,
                to=[user.email],
            )
            msg.attach_alternative(html_body, 'text/html')
            msg.send(fail_silently=False)
        except Exception as exc:
            logger.error('Failed to send activation email to %s: %s', user.email, exc)


# ── Plans ─────────────────────────────────────────────────────────────────────

class PlatformPlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [IsPlatformAdmin]


class PlatformSettingsView(APIView):
    """
    GET/PATCH /rest/v1/platform/settings/

    Singleton: siempre devuelve/actualiza la única fila de PlatformSettings.
    Solo super admins. Estos ajustes aplican únicamente al panel del super admin
    y no afectan a los tenants ni al sitio público.
    """
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        obj = PlatformSettings.get_solo()
        return Response(PlatformSettingsSerializer(obj).data)

    def patch(self, request):
        obj = PlatformSettings.get_solo()
        serializer = PlatformSettingsSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PublicPlanSettingsView(APIView):
    """
    GET /rest/v1/platform/settings/public/

    Subset público de los ajustes (sin auth) — para que el login del panel
    pueda leer el platform_name, logo_url y primary_color antes de loguearse.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        obj = PlatformSettings.get_solo()
        return Response({
            'primary_color': obj.primary_color,
            'platform_name': obj.platform_name,
            'logo_url': obj.logo_url,
        })


class PublicPlanListView(APIView):
    """
    GET /rest/v1/plans/

    Lista pública de planes activos visibles. Cualquier usuario autenticado
    (admins de tenants incluidos) puede consumirla — la usa el panel admin
    para mostrar las opciones de upgrade.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Plan.objects.filter(is_active=True, is_public=True).order_by('sort_order', 'price_monthly')
        return Response(PlanSerializer(qs, many=True).data)


# ── Subscriptions ─────────────────────────────────────────────────────────────

class PlatformSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.select_related('tenant', 'plan', 'discount').all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsPlatformAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = self.request.query_params.get('tenant')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


# ── Discounts ─────────────────────────────────────────────────────────────────

class PlatformDiscountViewSet(viewsets.ModelViewSet):
    queryset = Discount.objects.prefetch_related('applicable_plans').all()
    serializer_class = DiscountSerializer
    permission_classes = [IsPlatformAdmin]
