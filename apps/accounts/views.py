import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.crypto import get_random_string


logger = logging.getLogger(__name__)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Membership, MembershipRole, InvitationToken, PasswordChangeRequired, UserProfile
from apps.accounts.permissions import IsTenantAdminOrOwner, IsTenantMember
from apps.accounts.serializers import (
    TenantRegistrationSerializer,
    MembershipSerializer,
    InvitationCreateSerializer,
    InvitationTokenSerializer,
    MeSerializer,
)
from apps.tenants.models import Tenant
from apps.tenants.serializers import TenantPublicSerializer

User = get_user_model()


class ActivateAccountView(APIView):
    """
    POST /rest/v1/accounts/activate/{token}/

    Flujo de activación de cuenta para tenants creados desde el panel del super admin.
    Recibe el token de invitación → marca al usuario asociado como is_active=True
    → marca la invitación como aceptada.

    Idempotente: si ya está activada, devuelve 200 con un flag.
    """
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, token=None):
        try:
            invitation = InvitationToken._all.select_related('tenant').get(token=token)
        except InvitationToken.DoesNotExist:
            return Response({'error': 'Enlace de activación inválido.'}, status=status.HTTP_404_NOT_FOUND)

        if invitation.is_expired:
            return Response(
                {'error': 'El enlace de activación expiró. Pedile al super admin que reenvíe la invitación.'},
                status=status.HTTP_410_GONE,
            )

        try:
            user = User.objects.get(email=invitation.email)
        except User.DoesNotExist:
            return Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        already = user.is_active and invitation.is_accepted
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])
        if not invitation.is_accepted:
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=['accepted_at'])

        return Response({
            'activated': True,
            'already_active': already,
            'tenant_slug': invitation.tenant.slug,
            'tenant_name': invitation.tenant.name,
            'email': user.email,
        })


class TenantRegistrationView(APIView):
    """
    POST /rest/v1/accounts/register/

    Creates a Tenant, its owner User, and the owner Membership in one atomic transaction.
    Returns JWT tokens so the user is immediately authenticated.
    """
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = TenantRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        tenant = Tenant.objects.create(
            slug=data['tenant_slug'],
            name=data['tenant_name'],
            type=data['tenant_type'],
        )

        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
        )

        Membership._all.create(
            tenant=tenant,
            user=user,
            role=MembershipRole.OWNER,
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'tenant': TenantPublicSerializer(tenant).data,
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """
    GET /rest/v1/accounts/me/

    Returns the authenticated user with all their tenant memberships.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        allowed = ('first_name', 'last_name', 'email')
        for f in allowed:
            if f in request.data:
                setattr(user, f, request.data[f])
        # Optional password change — al cambiarla, limpiamos el flag de cambio obligatorio.
        if 'password' in request.data and request.data['password']:
            user.set_password(request.data['password'])
            PasswordChangeRequired.objects.filter(user=user).delete()
        user.save()
        return Response(MeSerializer(user).data)


class ProfilePictureView(APIView):
    """
    POST   /rest/v1/accounts/me/profile-picture/  → multipart con campo `image`
    DELETE /rest/v1/accounts/me/profile-picture/  → borra la foto actual
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        image = request.FILES.get('image')
        if not image:
            return Response({'detail': 'Subí un archivo en el campo "image".'}, status=400)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.profile_picture = image
        profile.save(update_fields=['profile_picture', 'updated_at'])
        url = profile.profile_picture.url if profile.profile_picture else None
        return Response({'profile_picture_url': request.build_absolute_uri(url) if url else None})

    def delete(self, request):
        profile = UserProfile.objects.filter(user=request.user).first()
        if profile and profile.profile_picture:
            profile.profile_picture.delete(save=False)
            profile.profile_picture = None
            profile.save(update_fields=['profile_picture', 'updated_at'])
        return Response(status=204)


class MembershipViewSet(viewsets.ModelViewSet):
    """
    CRUD for memberships within the current tenant.
    Read access for any member; write access requires admin/owner.
    """
    serializer_class = MembershipSerializer
    http_method_names = ['get', 'patch', 'delete', 'options', 'head']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsTenantMember()]
        return [IsTenantAdminOrOwner()]

    def get_queryset(self):
        return Membership.objects.for_tenant(self.request.tenant).select_related('user')

    def perform_destroy(self, instance):
        if instance.role == MembershipRole.OWNER:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('No se puede eliminar al propietario del tenant.')
        instance.is_active = False
        instance.save(update_fields=['is_active'])


class InvitationViewSet(viewsets.ViewSet):
    """
    Invitation flow for adding members to the current tenant.

    POST   /rest/v1/accounts/invitations/                → create invitation + send email
    GET    /rest/v1/accounts/invitations/                → list pending invitations
    DELETE /rest/v1/accounts/invitations/{id}/           → cancel pending invitation
    POST   /rest/v1/accounts/invitations/accept/{token}/ → accept invitation (public)
    """

    def get_permissions(self):
        if self.action == 'accept':
            return [AllowAny()]
        return [IsTenantAdminOrOwner()]

    def list(self, request):
        qs = InvitationToken.objects.for_tenant(request.tenant).filter(accepted_at__isnull=True)
        serializer = InvitationTokenSerializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = InvitationCreateSerializer(
            data=request.data,
            context={'tenant': request.tenant},
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        invitation = InvitationToken._all.create(
            tenant=request.tenant,
            email=data['email'],
            role=data['role'],
            invited_by=request.user,
        )

        self._send_invitation_email(invitation, request)

        return Response(InvitationTokenSerializer(invitation).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        """
        Cancela una invitación pendiente. Solo permitido si aún no fue aceptada;
        las aceptadas se gestionan a través del Membership ya creado.
        """
        try:
            invitation = InvitationToken.objects.for_tenant(request.tenant).get(pk=pk)
        except (InvitationToken.DoesNotExist, ValueError):
            return Response({'detail': 'Invitación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        if invitation.is_accepted:
            return Response(
                {'detail': 'No se puede cancelar una invitación ya aceptada.'},
                status=status.HTTP_409_CONFLICT,
            )
        invitation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='accept/(?P<token>[^/.]+)', permission_classes=[AllowAny])
    def accept(self, request, token=None):
        try:
            invitation = InvitationToken._all.select_related('tenant').get(token=token)
        except InvitationToken.DoesNotExist:
            return Response({'error': 'Invitación no válida.'}, status=status.HTTP_404_NOT_FOUND)

        if invitation.is_expired:
            return Response({'error': 'Esta invitación ha expirado.'}, status=status.HTTP_410_GONE)

        if invitation.is_accepted:
            return Response({'error': 'Esta invitación ya fue aceptada.'}, status=status.HTTP_409_CONFLICT)

        with transaction.atomic():
            try:
                user = User.objects.get(email=invitation.email)
                created = False
            except User.DoesNotExist:
                user = User.objects.create_user(
                    email=invitation.email,
                    password=get_random_string(16),
                )
                created = True

            membership, _ = Membership._all.get_or_create(
                tenant=invitation.tenant,
                user=user,
                defaults={'role': invitation.role, 'invited_by': invitation.invited_by},
            )

            # Si la invitación es para rol doctor, también creamos el perfil en
            # catalog/Doctor para que aparezca en /doctors y se le pueda asignar
            # horarios, especialidad, etc. El admin puede completar los detalles después.
            if invitation.role == MembershipRole.DOCTOR:
                from apps.catalog.models import Doctor
                Doctor._all.get_or_create(
                    tenant=invitation.tenant,
                    user=user,
                    defaults={'specialty': '', 'appointment_duration': 30},
                )

            # Si el usuario aceptó la invitación con una contraseña nueva, la aplicamos
            new_password = (request.data.get('password') or '').strip()
            if new_password:
                if len(new_password) < 8:
                    return Response(
                        {'error': 'La contraseña debe tener al menos 8 caracteres.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user.set_password(new_password)
                user.save(update_fields=['password'])

            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=['accepted_at'])

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'created': created,
            'tenant': TenantPublicSerializer(invitation.tenant).data,
        })

    @staticmethod
    def _send_invitation_email(invitation: InvitationToken, request):
        from shared.colors import darken, normalize_hex

        # URL del frontend admin del tenant — el flow de aceptar es una página Vue,
        # no el endpoint REST.
        template = getattr(settings, 'ADMIN_BASE_URL_TEMPLATE', 'http://admin.{slug}.miapp.com:3002')
        admin_base = template.format(slug=invitation.tenant.slug)
        accept_url = f'{admin_base}/aceptar-invitacion/{invitation.token}'

        # Nombre de la plataforma desde PlatformSettings (fallback genérico)
        try:
            from apps.platform.models import PlatformSettings
            platform_name = PlatformSettings.get_solo().platform_name or 'Agendamiento SaaS'
        except Exception:
            platform_name = 'Agendamiento SaaS'

        # Color del tenant (definido en su branding) — fallback al sage default.
        tenant_color = (invitation.tenant.settings or {}).get('branding', {}).get('primaryColor') or '#6FA776'
        primary_color = normalize_hex(tenant_color, fallback='#6FA776')
        primary_color_dark = darken(primary_color, amount=0.18)

        ctx = {
            'tenant_name': invitation.tenant.name,
            'tenant_slug': invitation.tenant.slug,
            'role_display': invitation.get_role_display(),
            'email': invitation.email,
            'accept_url': accept_url,
            'platform_name': platform_name,
            'primary_color': primary_color,
            'primary_color_dark': primary_color_dark,
        }

        subject = f'Invitación a {invitation.tenant.name}'
        text_body = render_to_string('accounts/emails/invitation.txt', ctx)
        html_body = render_to_string('accounts/emails/invitation.html', ctx)

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=None,
                to=[invitation.email],
            )
            msg.attach_alternative(html_body, 'text/html')
            msg.send(fail_silently=False)
        except Exception as exc:
            logger.error('Failed to send invitation email to %s: %s', invitation.email, exc)
